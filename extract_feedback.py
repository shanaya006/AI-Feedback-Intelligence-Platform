"""
Step 2: LLM Extraction Pipeline
Turns raw Swiggy reviews into structured PM signal.

SETUP:
1. python3 -m pip install google-genai pandas
2. Get an API key: https://aistudio.google.com/apikey
3. Set it as an environment variable:
     export GEMINI_API_KEY="your-key-here"
4. Run: python3 extract_feedback.py

This processes swiggy_sample_2000.csv and writes reviews_enriched.csv

HOW TO RESUME IF THE SCRIPT STOPS (crash, closed terminal, laptop sleep, etc.):
Open reviews_enriched.csv, check the last review_id that was saved, then set
START_ROW to that row number before rerunning — it will pick up from there
instead of starting over and wasting your rate limit re-processing done rows.
"""

import pandas as pd
from google import genai
from google.genai import types
import json
import time
import os

# ---------- CONFIG ----------
INPUT_FILE = "swiggy_sample_2000.csv"
OUTPUT_FILE = "reviews_enriched.csv"
MODEL = "gemini-3.5-flash-lite"
BATCH_SAVE_EVERY = 50
START_ROW = 380                  # continuing from yesterday's completed batch (rows 0-380 done)
LIMIT = 500                      # TODAY: takes you to 880 total (380 + 500 = 880)
# This is your FINAL planned batch. After this completes, move to Step 3: theme clustering.

# Your confirmed free-tier limit is 15 RPM (checked in AI Studio -> Rate Limit).
# We pace at 5 seconds/call = 12 requests/minute, leaving a safety buffer so we
# don't ride the exact edge of the limit and trip a 429.
SECONDS_BETWEEN_CALLS = 5
MAX_RETRIES = 4                 # retries per review if rate-limited
RETRY_BACKOFF_SECONDS = 30      # wait this long (x attempt number) after a 429 before retrying

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# ---------- PROMPT ----------
SYSTEM_PROMPT = """You are a product analyst extracting structured signal from a customer review
of a food delivery app (Swiggy). Return ONLY valid JSON matching this schema exactly.
Do not add any commentary, markdown formatting, or code fences — just the raw JSON object.

Schema:
{
  "sentiment": "positive | negative | neutral | mixed",
  "pain_point": "string or null - the specific problem described, in plain language",
  "feature_request": "string or null - explicit or clearly implied feature ask",
  "topic": "string - one of: Delivery Time, Order Accuracy, Refunds & Payments, Customer Support, App Bugs/UX, Pricing & Offers, Delivery Partner Behavior, Instamart, Restaurant Quality, Account/Login, Other",
  "urgency": "low | medium | high | critical",
  "user_segment": "string or null - e.g. 'long-term user', 'new user', 'Instamart user'",
  "competitor_mention": "string or null - competitor name if referenced",
  "churn_risk": "low | medium | high | unknown",
  "churn_signal_phrase": "string or null - exact phrase indicating churn intent",
  "suggested_opportunity": "string - one sentence describing a broader product opportunity",
  "confidence": "float between 0 and 1 - realistic confidence in this extraction"
}

IMPORTANT RULES:

1. CHURN RISK:
Be extremely conservative when assigning churn risk.

Only assign:
- "high" = the user explicitly says they will stop using Swiggy,
  uninstall/delete the app, switch to a competitor, or stop ordering
  from Swiggy.
- "medium" = the user explicitly indicates they may leave or stop
  using Swiggy if the problem continues, but has not yet decided to leave.
- "low" = the user expresses a mild indication of possible future
  disengagement, but there is no clear intent to leave.
- "unknown" = there is no explicit evidence of churn intent.

IMPORTANT:
Negative sentiment, a 1-star rating, anger, calling Swiggy "fake",
complaining about prices, warning others about a problem, or saying
"don't use this feature" do NOT automatically indicate churn.

Examples:
"I will never use Swiggy again" → high
"I'll order from Zomato instead" → high
"Better fix this or I'll stop using Swiggy" → medium
"Swiggy is terrible, worst app ever" → unknown
"Don't pay online on Swiggy" → unknown
"Very expensive" → unknown

If churn_risk is "unknown", churn_signal_phrase MUST be null.

2. USER SEGMENT:
Only assign a user segment when there is explicit evidence in the review.

Examples:
"I've been using Swiggy for 5 years" → long-term user
"I just downloaded the app" → new user
"My Instamart order..." → Instamart user

Do NOT infer a segment from rating, writing style, complaint type,
or assumptions.

If there is insufficient evidence, return null.

3. URGENCY:
Do not determine urgency solely from the star rating.

- critical = immediate serious issue such as money lost, safety issue,
  account access failure, or a major service failure requiring immediate
  intervention.
- high = significant problem likely to strongly affect the user's
  experience or trust.
- medium = meaningful but non-critical problem.
- low = minor inconvenience, suggestion, praise, or cosmetic issue.

4. SENTIMENT:
Judge sentiment from the actual text, not just the star rating.
The star rating is supporting context, not the sole determinant.

5. FEATURE REQUEST:
Only provide a feature_request when the user explicitly asks for something
OR a clear product improvement is directly implied by the complaint.
Otherwise return null.

6. TOPIC:
Use the most specific topic available.

- Restaurant Quality = food taste, freshness, spoiled food, portion size,
  food quality, or restaurant-specific food problems.
- Pricing & Offers = prices, delivery fees, discounts, coupons, offers,
  or perceived value.
- Delivery Time = late delivery, ETA accuracy, waiting time, or delays.
- Order Accuracy = wrong, missing, swapped, or incorrect items.
- Refunds & Payments = payment failures, payment methods, refunds,
  duplicate charges, or billing problems.
- Customer Support = inability to reach support or poor support response.
- App Bugs/UX = crashes, UI problems, maps, location bugs, navigation,
  notifications, or other app functionality problems.
- Delivery Partner Behavior = rider behavior, professionalism, conduct,
  or communication.
- Instamart = problems specifically related to Instamart.
- Account/Login = login, account access, OTP, or account-related issues.
- Other = use only when none of the above topics reasonably fit.

Do NOT classify restaurant availability, restaurant selection, or restaurant
coverage as Restaurant Quality.

7. SUGGESTED OPPORTUNITY:
This should describe a broader product opportunity, not simply repeat
the user's complaint.

Example:
Complaint: "Delivery was 45 minutes late."
Weak opportunity: "Fix late delivery."
Better opportunity: "Improve delivery ETA prediction and exception handling
to reduce late-order incidents."

8. CONFIDENCE:
Return a realistic confidence score between 0 and 1.
Do not default to 0.95.
Use lower confidence when the review is vague, ambiguous, contains multiple
unrelated issues, or is difficult to interpret.
"""

def extract_review(review_text, rating):
    full_prompt = f'{SYSTEM_PROMPT}\n\nReview: "{review_text}"\nStar rating: {rating}'

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=500,
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )

            raw_text = response.text.strip()
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()

            return json.loads(raw_text)

        except json.JSONDecodeError:
            print("  [WARN] Failed to parse JSON, skipping this review.")
            return None  # not a rate-limit issue, no point retrying

        except Exception as e:
            err_str = str(e)
            is_rate_limit = "429" in err_str or "quota" in err_str.lower() or "RESOURCE_EXHAUSTED" in err_str

            if is_rate_limit and attempt < MAX_RETRIES:
                wait_time = RETRY_BACKOFF_SECONDS * attempt
                print(f"  [RATE LIMIT] Attempt {attempt}/{MAX_RETRIES} failed. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            elif is_rate_limit:
                print(f"  [RATE LIMIT] Gave up after {MAX_RETRIES} attempts. "
                      f"Check https://aistudio.google.com/apikey for your live quota before running again.")
                return None
            else:
                print(f"  [ERROR] {e}")
                return None

    return None


def main():
    df = pd.read_csv(INPUT_FILE)

    if LIMIT:
        df = df.iloc[START_ROW:START_ROW + LIMIT]
    else:
        df = df.iloc[START_ROW:]

    # Load any existing results so we APPEND instead of overwriting previous batches
    existing_results = []
    if os.path.exists(OUTPUT_FILE):
        existing_df = pd.read_csv(OUTPUT_FILE)
        existing_results = existing_df.to_dict("records")
        print(f"Found {len(existing_results)} existing rows in {OUTPUT_FILE} — will append to these.\n")

    results = []
    total = len(df)
    start_time = time.time()

    print(f"Processing {total} reviews...")
    print(f"Pacing at {SECONDS_BETWEEN_CALLS}s/call — estimated time: "
          f"{round(total * SECONDS_BETWEEN_CALLS / 60, 1)} minutes\n")

    for i, row in df.iterrows():

        extracted = extract_review(
            row["review_text"],
            row["rating"]
        )

        if extracted:
            extracted["review_id"] = row["review_id"]
            extracted["review_text"] = row["review_text"]
            extracted["rating"] = row["rating"]
            extracted["review_date"] = row["review_date"]

            results.append(extracted)

        if len(results) % 10 == 0 and results:
            elapsed_min = (time.time() - start_time) / 60
            print(f"  ...{len(results)}/{total} done ({elapsed_min:.1f} min elapsed)")

        # Save progress periodically (existing rows + everything processed so far this run)
        if len(results) % BATCH_SAVE_EVERY == 0 and results:
            combined = existing_results + results
            pd.DataFrame(combined).drop_duplicates(subset="review_id", keep="last").to_csv(
                OUTPUT_FILE,
                index=False
            )

        time.sleep(SECONDS_BETWEEN_CALLS)  # paced to stay under free-tier RPM limit

    # Final save — combine existing rows with this run's new rows
    combined_results = existing_results + results
    enriched_df = pd.DataFrame(combined_results).drop_duplicates(subset="review_id", keep="last")
    enriched_df = enriched_df.sort_values("review_id")

    if not enriched_df.empty:
        lead_cols = [
            "review_id",
            "review_text",
            "rating",
            "review_date"
        ]

        other_cols = [
            c for c in enriched_df.columns
            if c not in lead_cols
        ]

        enriched_df = enriched_df[lead_cols + other_cols]

    enriched_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"\nDone. {len(results)}/{total} new reviews processed this run."
    )
    print(f"Total rows in {OUTPUT_FILE} now: {len(enriched_df)}")

    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()