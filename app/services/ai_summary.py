import json
from typing import List, Dict, Any
from decimal import Decimal
from app.core.logging import logger
from app.core.gemini import gemini_client
from app.models.transaction import Transaction
from app.models.summary import JobSummary

class AISummaryService:
    @staticmethod
    def generate_summary(job_id: Any, transactions: List[Transaction]) -> JobSummary:
        """Calculates spending metrics, calls Gemini to generate narrative summary and risk assessment,
        and returns a populated JobSummary database object.
        """
        logger.info(f"Generating AI Summary for job {job_id}...")
        
        if not transactions:
            # Empty transaction list defaults
            return JobSummary(
                job_id=job_id,
                total_spend_inr=Decimal("0.00"),
                total_spend_usd=Decimal("0.00"),
                top_merchants=[],
                anomaly_count=0,
                narrative="No transactions to summarize.",
                risk_level="low"
            )

        # 1. Calculate metrics using python
        total_by_currency: Dict[str, float] = {}
        merchant_spend: Dict[str, float] = {}
        category_spend: Dict[str, float] = {}
        anomalies = []
        
        for t in transactions:
            curr = t.currency or "INR"
            amt = float(t.amount)
            
            # Currency spend
            total_by_currency[curr] = total_by_currency.get(curr, 0.0) + amt
            
            # Merchant spend
            merchant_spend[t.merchant] = merchant_spend.get(t.merchant, 0.0) + amt
            
            # Category spend (use llm_category if available, otherwise category)
            cat = t.llm_category or t.category
            category_spend[cat] = category_spend.get(cat, 0.0) + amt
            
            # Anomaly tracking
            if t.is_anomaly:
                anomalies.append({
                    "txn_id": t.txn_id,
                    "merchant": t.merchant,
                    "amount": amt,
                    "currency": curr,
                    "reason": t.anomaly_reason
                })

        # Calculate top 3 merchants by spend
        sorted_merchants = sorted(merchant_spend.items(), key=lambda x: x[1], reverse=True)
        top_3_merchants = [m[0] for m in sorted_merchants[:3]]
        
        # Calculate INR and USD totals (exchange rate 1 USD = 83 INR)
        total_inr = 0.0
        total_usd = 0.0
        for curr, amt in total_by_currency.items():
            if curr == "INR":
                total_inr += amt
                total_usd += amt / 83.0
            elif curr == "USD":
                total_usd += amt
                total_inr += amt * 83.0
            else:
                # Default conversion if other currency (assume same as INR for base fallback)
                total_inr += amt
                total_usd += amt / 83.0

        anomaly_count = len(anomalies)

        # 2. Build prompt for Gemini narrative and risk level
        system_instruction = (
            "You are a senior financial analyst and auditor. "
            "Your task is to write a concise (2-4 sentences), highly professional narrative summary analyzing the spending data "
            "and flagging any potential risks. Based on the data, classify the risk level as 'low', 'medium', or 'high'. "
            "You must return a JSON response matching the required structure exactly. Do not invent numbers."
        )

        input_data = {
            "total_spend_by_currency": total_by_currency,
            "top_3_merchants": top_3_merchants,
            "anomaly_count": anomaly_count,
            "anomalies_flagged": anomalies[:5],  # send up to 5 anomaly details
            "category_distribution": category_spend
        }

        prompt = (
            f"Analyze this financial transaction job data and populate the narrative and risk_level fields. "
            f"Please keep the computed aggregates exactly as provided.\n"
            f"Input Data:\n{json.dumps(input_data, indent=2)}\n\n"
            f"Required Output JSON format:\n"
            f"{{\n"
            f"  \"total_spend_by_currency\": {{ ... }},\n"
            f"  \"top_3_merchants\": [ ... ],\n"
            f"  \"anomaly_count\": {anomaly_count},\n"
            f"  \"narrative\": \"Write a professional narrative analyzing categories, trends and anomalies here.\",\n"
            f"  \"risk_level\": \"low|medium|high\"\n"
            f"}}"
        )

        narrative = "No analysis generated."
        risk_level = "low"

        try:
            raw_response = gemini_client.generate_json_response(
                prompt=prompt,
                system_instruction=system_instruction
            )
            
            summary_data = json.loads(raw_response)
            narrative = summary_data.get("narrative", f"Processed {len(transactions)} transactions with {anomaly_count} anomalies.")
            risk_level = summary_data.get("risk_level", "low").lower()
            
            if risk_level not in {"low", "medium", "high"}:
                risk_level = "medium" if anomaly_count > 0 else "low"
                
        except Exception as e:
            logger.error(f"Failed to generate narrative summary using Gemini: {e}. Using rule-based fallback.")
            # Fallback narrative
            if anomaly_count > 0:
                risk_level = "high" if anomaly_count > 3 else "medium"
                narrative = (
                    f"Audit warning: Flagged {anomaly_count} anomalous transactions. "
                    f"Top spending was on merchants: {', '.join(top_3_merchants)}. "
                    f"Review transactions immediately."
                )
            else:
                risk_level = "low"
                narrative = (
                    f"Spending patterns normal across {len(transactions)} transactions. "
                    f"Top spending merchants include {', '.join(top_3_merchants)}."
                )

        return JobSummary(
            job_id=job_id,
            total_spend_inr=Decimal(f"{total_inr:.2f}"),
            total_spend_usd=Decimal(f"{total_usd:.2f}"),
            top_merchants=top_3_merchants,
            anomaly_count=anomaly_count,
            narrative=narrative,
            risk_level=risk_level
        )
