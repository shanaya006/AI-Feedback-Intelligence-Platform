# AI Feedback Intelligence Platform

### LLM-Powered Customer Feedback Analysis & Product Prioritization

Turning unstructured Swiggy customer reviews into structured product signals, actionable insights, and a prioritized product opportunity.

---

## 📎 Project Links

- **[Live Dashboard](https://swiggy-dashboard-sable.vercel.app)**
- **[Product Case Study](https://s.craft.me/Q0pkrfZuBEJerD)**
- **[Full PRD](https://docs.google.com/document/d/1B-1KYx9UVgX_khBCDtDCq4-dl2Mdq5QxdjcbnhwbMUc/edit?usp=sharing)**

---

## 🎯 The Problem

Customer reviews contain valuable signals about pain points, feature requests, sentiment, and churn — but raw feedback is difficult to systematically analyze at scale.

This project explores how an LLM can transform unstructured customer feedback into structured signals that can support product discovery and prioritization.

---

## 🔬 Approach

**205K+ Reviews** → **880 Reviews** → **Gemini LLM** → **Structured Feedback** → **SQL Analysis** → **RICE Prioritization** → **Product Proposal**

Gemini was used to extract attributes such as sentiment, topic, urgency, pain points, feature requests, churn risk, competitor mentions, and suggested opportunities.

The enriched dataset was then analyzed using SQLite to identify patterns across **volume, severity, sentiment, and churn risk**.

---

## 📊 Key Findings

Complaint volume alone did not indicate the highest-impact opportunity.

| Topic | Reviews | Negative | Severe |
|---|---:|---:|---:|
| Delivery Time | 171 | 62.0% | 34.5% |
| Refunds & Payments | 74 | 86.5% | 68.9% |
| Customer Support | 72 | 91.7% | 63.9% |
| Order Accuracy | 30 | 86.7% | 70.0% |

The analysis highlighted **Refunds & Payments + Customer Support** as a connected opportunity in the post-order resolution journey.


<img width="1470" height="956" alt="Screenshot 2026-09-19 at 12 22 53 AM" src="https://github.com/user-attachments/assets/7dfa8b2f-cf4f-49c1-8db9-009eead811b6" />
<img width="1470" height="956" alt="Screenshot 2026-09-19 at 12 22 59 AM" src="https://github.com/user-attachments/assets/752246d7-b023-4fc8-a136-3a80cff0d65e" />
<img width="1470" height="956" alt="Screenshot 2026-09-19 at 12 23 15 AM" src="https://github.com/user-attachments/assets/8f61fc06-6eba-4d4f-92dd-8852d8079388" />


---

## 💡 Product Proposal

### ResolveFlow
**An AI-Powered Customer Dispute Resolution & Escalation Platform**

A proposed decisioning layer that:

- Verifies customer issues using available signals
- Automatically resolves clear, low-risk cases
- Routes ambiguous cases to human agents
- Dynamically escalates unresolved issues
- Gives support agents consolidated case context and recommended actions

The goal is to make issue resolution **faster, more consistent, and appropriately automated**.

---

## 🛠️ Tech Stack

**Gemini LLM · SQLite · SQL · HTML · CSS · JavaScript · RICE**

---

