/*
 * The RFM analysis is a marketing technique used to quantitatively rank and group customers based on their purchasing behavior.
 * It helps businesses identify their most valuable customers and tailor marketing strategies accordingly.
 * The RFM model is based on three key metrics:
 * - Recency: How recently a customer has made a purchase.
 * - Frequency: How often a customer makes a purchase.
 * - Monetary: How much money a customer spends on purchases.

 * This model creates a fact table for customer RFM (Recency, Frequency, Monetary) analysis.
 * It calculates the last order date, frequency of orders, and monetary value for each customer.
 * It also assigns RFM scores and segments customers based on their RFM values.
 * One row per unique customer ID
 
| Dimension         | Distribution / Observation                                         | Scoring Method         |   Score |
| ----------------- | ------------------------------------------------------------------ | ---------------------- | ------: |
| **Recency (R)**   | Widely distributed and skewed; no natural cutoff intervals         | Percentile             | **1–5** |
| **Frequency (F)** | 96.96% of customers have only one order; very few repeat customers | Business-defined bands | **1–4** |
| **Monetary (M)**  | Strong right skew with extreme high-value outliers                 | Percentile             | **1–5** |

| Dimension     |  Score  |
| ------------- | --------|
| **Recency**   |  1–5    |
| **Frequency** |  1–4    |
| **Monetary**  |  1–5    |

 * Recency is calculated as the number of days since the last order date.
 * RFM Analysis Date: 2018-10-18, selected as the day immediately following the Olist latest transaction date.

Recency scoring
| Percentile rank of Recency | Recency score | Meaning                        |
| -------------------------- | ------------: | ------------------------------ |
| 0–20%                      |         **5** | Most recently active customers |
| >20–40%                    |         **4** | Relatively recent              |
| >40–60%                    |         **3** | Average recency                |
| >60–80%                    |         **2** | Relatively inactive            |
| >80–100%                   |         **1** | Least recently active          |

Freqency scoring
| Frequency | Score | Interpretation         |
| --------: | ----: | ---------------------- |
|   1 order | **1** | One-time customer      |
|  2 orders | **2** | Repeat customer        |
|  3 orders | **3** | Frequent customer      |
| 4+ orders | **4** | Highly repeat customer |

Monetary Scoring
| Percentile rank of Monetary | Score | Meaning                 |
| --------------------------- | ----: | ----------------------- |
| 0–20%                       | **1** | Lowest-value customers  |
| >20–40%                     | **2** | Low-value customers     |
| >40–60%                     | **3** | Average-value customers |
| >60–80%                     | **4** | High-value customers    |
| >80–100%                    | **5** | Highest-value customers |

| Dimension     | Score 1      | Score 2  | Score 3  | Score 4   | Score 5     |
| ------------- | ------------ | -------- | -------- | --------- | ----------- |
| **Recency**   | Least recent |          | Average  |           | Most recent |
| **Frequency** | 1 order      | 2 orders | 3 orders | 4+ orders | —           |
| **Monetary**  | Lowest 20%   | 20–40%   | 40–60%   | 60–80%    | Highest 20% |

| Segment                           | Recency (R) | Frequency (F) | Monetary (M) | Customer Profile                                      | Suggested Action                       |
| --------------------------------- | ----------: | ------------: | -----------: | ----------------------------------------------------- | -------------------------------------- |
| **Champions**                     |         ≥ 4 |           ≥ 4 |          ≥ 4 | Recent, frequent, high-value customers                | Reward, VIP treatment, loyalty program |
| **Loyal Customers**               |         ≥ 4 |           ≥ 3 |          Any | Frequent and active customers                         | Retention, cross-sell                  |
| **Big Spenders**                  |         ≥ 3 |           Any |          = 5 | High-value customers                                  | Premium offers, exclusive products     |
| **Recent One-Time Customers**     |         ≥ 4 |           = 1 |          Any | Recent first-time buyers                              | Encourage second purchase              |
| **Potential Loyalists**           |         ≥ 4 |             2 |          Any | Recent repeat customers with growth potential         | Loyalty incentives                     |
| **At Risk**                       |         2–3 |           ≥ 3 |          Any | Previously engaged repeat customers becoming inactive | Win-back campaign                      |
| **Needs Attention**               |         2–3 |           ≤ 2 |          Any | Low-frequency customers showing declining engagement  | Personalized promotion                 |
| **Lost Customers**                |         = 1 |           Any |          Any | Long-inactive customers                               | Reactivation campaign                  |


*/

WITH customer_metrics AS 
(
    SELECT
        customer_key,
        DATE('2018-10-18') AS analysis_date,
        DATE_DIFF(
            DATE('2018-10-18'),
            DATE(MAX(order_purchase_timestamp)),
            DAY
        ) AS recency,
        COUNT(DISTINCT order_id) AS frequency,
        SUM(gross_merchandise_value) AS monetary
    FROM {{ ref('fact_orders') }} 
    WHERE order_status NOT IN (
        'CANCELED',
        'UNAVAILABLE'
    )
    GROUP BY customer_key
),

scored AS 
(
    SELECT
        *,
        
        CASE
            WHEN PERCENT_RANK() OVER (
                ORDER BY recency ASC
            ) <= 0.20 THEN 5

            WHEN PERCENT_RANK() OVER (
                ORDER BY recency ASC
            ) <= 0.40 THEN 4

            WHEN PERCENT_RANK() OVER (
                ORDER BY recency ASC
            ) <= 0.60 THEN 3

            WHEN PERCENT_RANK() OVER (
                ORDER BY recency ASC
            ) <= 0.80 THEN 2

            ELSE 1
        END AS recency_score,

        CASE
            WHEN frequency = 1 THEN 1
            WHEN frequency = 2 THEN 2
            WHEN frequency = 3 THEN 3
            WHEN frequency >= 4 THEN 4
        END AS frequency_score,

        CASE
            WHEN PERCENT_RANK() OVER (
                ORDER BY monetary ASC
            ) <= 0.20 THEN 1

            WHEN PERCENT_RANK() OVER (
                ORDER BY monetary ASC
            ) <= 0.40 THEN 2

            WHEN PERCENT_RANK() OVER (
                ORDER BY monetary ASC
            ) <= 0.60 THEN 3

            WHEN PERCENT_RANK() OVER (
                ORDER BY monetary ASC
            ) <= 0.80 THEN 4
            ELSE 5
        END AS monetary_score

    FROM customer_metrics
)

SELECT
    *,

    CONCAT(
        CAST(recency_score AS STRING),
        CAST(frequency_score AS STRING),
        CAST(monetary_score AS STRING)
    ) AS rfm_code,

    recency_score
        + frequency_score
        + monetary_score AS rfm_total_score,

    CASE
        WHEN recency_score >= 4
         AND frequency_score >= 4
         AND monetary_score >= 4
            THEN 'Champions'

        WHEN recency_score >= 4
         AND frequency_score >= 3
            THEN 'Loyal Customers'

        WHEN monetary_score = 5
         AND recency_score >= 3
            THEN 'Big Spenders'

        WHEN frequency_score = 1
         AND recency_score >= 4
            THEN 'Recent One-Time Customers'

        WHEN recency_score >= 4
         AND frequency_score = 2
            THEN 'Potential Loyalists'

        WHEN recency_score BETWEEN 2 AND 3
            AND frequency_score >= 3
            THEN 'At Risk'

        WHEN recency_score BETWEEN 2 AND 3
         AND frequency_score <= 2
            THEN 'Needs Attention'

        WHEN recency_score = 1
            THEN 'Lost Customers'

        ELSE 'Other'
    END AS customer_segment

FROM scored