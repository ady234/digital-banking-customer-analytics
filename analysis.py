from pathlib import Path
import csv


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
PRIMARY_DATA_PATH = DATA_DIR / "bank_customer_behavior_and_churn.csv"
FALLBACK_DATA_PATH = DATA_DIR / "digital_banking_customers.csv"
MAX_HIGH_RISK_PREVIEW = 15


def get_data_path() -> Path:
    if PRIMARY_DATA_PATH.exists():
        return PRIMARY_DATA_PATH
    return FALLBACK_DATA_PATH


def load_data() -> list[dict]:
    data_path = get_data_path()

    with data_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if rows and "full_name" in rows[0]:
        integer_fields = {
            "customer_id",
            "age",
            "credit_sco",
            "tenure",
            "balance",
            "products_number",
            "credit_card",
            "active_member",
            "estimated_salary",
            "complaint_count",
            "engagement_score",
            "risk_score",
            "exit",
        }
        float_fields = {"monthly_income", "monthly_outgoing"}
    else:
        integer_fields = {
            "age",
            "tenure_months",
            "monthly_transactions",
            "avg_login_days_per_month",
            "products_held",
            "complaint_count",
            "support_tickets",
            "engagement_score",
            "churned",
            "churn_probability",
        }
        float_fields = {"avg_balance"}

    for row in rows:
        for field in integer_fields:
            if field in row and row[field] != "":
                row[field] = int(float(row[field]))
        for field in float_fields:
            if field in row and row[field] != "":
                row[field] = float(row[field])

    return rows


def mean(values: list[float]) -> float:
    numeric_values = [
        float(value)
        for value in values
        if value not in ("", None)
    ]
    return sum(numeric_values) / len(numeric_values) if numeric_values else 0.0


def preview_limit(total_rows: int) -> int:
    return MAX_HIGH_RISK_PREVIEW if total_rows > 100 else total_rows


def using_kaggle_schema(rows: list[dict]) -> bool:
    return bool(rows) and "full_name" in rows[0]


def classify_risk(row: dict) -> str:
    if "risk_segment" in row and row["risk_segment"]:
        return row["risk_segment"]

    if "risk_score" in row:
        if row["risk_score"] >= 75:
            return "High Risk"
        if row["risk_score"] >= 45:
            return "Medium Risk"
        return "Low Risk"

    if (
        row["engagement_score"] < 35
        or row["complaint_count"] >= 3
        or row["avg_login_days_per_month"] < 5
    ):
        return "High Risk"
    if row["engagement_score"] <= 60 or row["complaint_count"] == 2:
        return "Medium Risk"
    return "Low Risk"


def summarize(rows: list[dict]) -> None:
    print("Digital Banking Analytics Summary")
    print("-" * 35)
    print(f"Dataset: {get_data_path().name}")

    total_customers = len(rows)

    if using_kaggle_schema(rows):
        churn_rate = mean([row["exit"] for row in rows]) * 100
        avg_engagement = mean([row["engagement_score"] for row in rows])
        avg_risk = mean([row["risk_score"] for row in rows])

        print(f"Total customers: {total_customers}")
        print(f"Churn rate: {churn_rate:.2f}%")
        print(f"Average engagement score: {avg_engagement:.2f}")
        print(f"Average risk score: {avg_risk:.2f}")
        print()

        print("Average metrics by churn status")
        for churn_value in [0, 1]:
            group = [row for row in rows if row["exit"] == churn_value]
            print(
                f"Exited={churn_value}: "
                f"engagement={mean([row['engagement_score'] for row in group]):.2f}, "
                f"risk={mean([row['risk_score'] for row in group]):.2f}, "
                f"balance={mean([row['balance'] for row in group]):.2f}, "
                f"active_members={mean([row['active_member'] for row in group]):.2f}"
            )
        print()

        high_risk = [row for row in rows if classify_risk(row).lower() == "high risk"]

        print(f"High-risk customers identified: {len(high_risk)}")
        print(f"Previewing top {min(preview_limit(len(rows)), len(high_risk))} high-risk customers")
        for row in sorted(high_risk, key=lambda item: (-item.get("risk_score", 0), item["engagement_score"]))[
            : preview_limit(len(rows))
        ]:
            print(
                f"{row['customer_id']} | {row['full_name']} | balance={row['balance']:.0f} | "
                f"engagement={row['engagement_score']} | risk_score={row.get('risk_score', 0)} | "
                f"digital_behavior={row.get('digital_behavior', 'N/A')} | exit={row['exit']}"
            )
        return

    churn_rate = mean([row["churned"] for row in rows]) * 100
    avg_engagement = mean([row["engagement_score"] for row in rows])

    print(f"Total customers: {total_customers}")
    print(f"Churn rate: {churn_rate:.2f}%")
    print(f"Average engagement score: {avg_engagement:.2f}")
    print()

    print("Average metrics by churn status")
    for churn_value in [0, 1]:
        group = [row for row in rows if row["churned"] == churn_value]
        print(
            f"Churned={churn_value}: "
            f"engagement={mean([row['engagement_score'] for row in group]):.2f}, "
            f"transactions={mean([row['monthly_transactions'] for row in group]):.2f}, "
            f"logins={mean([row['avg_login_days_per_month'] for row in group]):.2f}, "
            f"complaints={mean([row['complaint_count'] for row in group]):.2f}"
        )
    print()

    high_risk = [row for row in rows if classify_risk(row) == "High Risk"]

    print(f"High-risk customers identified: {len(high_risk)}")
    print(f"Previewing top {min(preview_limit(len(rows)), len(high_risk))} high-risk customers")
    for row in sorted(high_risk, key=lambda item: (item["engagement_score"], -item["complaint_count"]))[
        : preview_limit(len(rows))
    ]:
        print(
            f"{row['customer_id']} | {row['customer_name']} | balance={row['avg_balance']:.0f} | "
            f"transactions={row['monthly_transactions']} | logins={row['avg_login_days_per_month']} | "
            f"complaints={row['complaint_count']} | engagement={row['engagement_score']} | churned={row['churned']}"
        )


def search_customer(rows: list[dict], search_text: str) -> list[dict]:
    query = search_text.strip().lower()
    if using_kaggle_schema(rows):
        return [
            row
            for row in rows
            if query in str(row["full_name"]).lower() or query in str(row["customer_id"]).lower()
        ]
    return [
        row
        for row in rows
        if query in row["customer_name"].lower() or query in row["customer_id"].lower()
    ]


def display_customer_details(matches: list[dict], rows: list[dict]) -> None:
    if not matches:
        print("No customer found with that name or ID.")
        return

    kaggle_schema = using_kaggle_schema(rows)
    if len(matches) > 20:
        print(f"Found {len(matches)} matches. Showing the first 20 results only.")
        matches = matches[:20]

    for row in matches:
        print()
        if kaggle_schema:
            print(f"Customer ID: {row['customer_id']}")
            print(f"Customer Name: {row['full_name']}")
            print(f"Country: {row.get('country', 'N/A')}")
            print(f"Gender: {row.get('gender', 'N/A')}")
            print(f"Age: {row.get('age', 'N/A')}")
            print(f"Tenure: {row.get('tenure', 'N/A')}")
            print(f"Balance: {row.get('balance', 0):.2f}")
            print(f"Products Number: {row.get('products_number', 'N/A')}")
            print(f"Active Member: {'Yes' if row.get('active_member', 0) == 1 else 'No'}")
            print(f"Digital Behavior: {row.get('digital_behavior', 'N/A')}")
            print(f"Engagement Score: {row.get('engagement_score', 'N/A')}")
            print(f"Risk Score: {row.get('risk_score', 'N/A')}")
            print(f"Risk Segment: {classify_risk(row)}")
            print(f"Exited: {'Yes' if row.get('exit', 0) == 1 else 'No'}")
        else:
            print(f"Customer ID: {row['customer_id']}")
            print(f"Customer Name: {row['customer_name']}")
            print(f"City: {row['city']}")
            print(f"Account Type: {row['account_type']}")
            print(f"Tenure (months): {row['tenure_months']}")
            print(f"Average Balance: {row['avg_balance']:.2f}")
            print(f"Monthly Transactions: {row['monthly_transactions']}")
            print(f"Login Days/Month: {row['avg_login_days_per_month']}")
            print(f"Products Held: {row['products_held']}")
            print(f"Complaint Count: {row['complaint_count']}")
            print(f"Engagement Score: {row['engagement_score']}")
            if "churn_probability" in row:
                print(f"Churn Probability: {row['churn_probability']}%")
            print(f"Churned: {'Yes' if row['churned'] == 1 else 'No'}")
            print(f"Risk Segment: {classify_risk(row)}")
            if "suggested_action" in row:
                print(f"Suggested Action: {row['suggested_action']}")


def run_menu(rows: list[dict]) -> None:
    while True:
        print()
        print("Digital Banking Analytics Menu")
        print("1. View summary")
        print("2. Search customer by name or ID")
        print("3. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            print()
            summarize(rows)
        elif choice == "2":
            search_text = input("Insert customer name or ID: ").strip()
            matches = search_customer(rows, search_text)
            display_customer_details(matches, rows)
        elif choice == "3":
            print("Exiting analytics menu.")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    customer_rows = load_data()
    run_menu(customer_rows)
