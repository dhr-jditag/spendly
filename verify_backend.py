"""Verification script to test the backend connection implementation."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown
)

print("=" * 60)
print("BACKEND CONNECTION VERIFICATION")
print("=" * 60)

# Test with demo user (user_id = 1)
user_id = 1

print("\n1. Testing get_user_by_id()...")
user_info = get_user_by_id(user_id)
if user_info:
    print(f"   ✓ Name: {user_info['name']}")
    print(f"   ✓ Email: {user_info['email']}")
    print(f"   ✓ Member since: {user_info['member_since']}")
else:
    print("   ✗ User not found!")

print("\n2. Testing get_summary_stats()...")
summary_stats = get_summary_stats(user_id)
print(f"   ✓ Total Spent: ₹{summary_stats['total_spent']:.2f}")
print(f"   ✓ Transaction Count: {summary_stats['transaction_count']}")
print(f"   ✓ Top Category: {summary_stats['top_category']}")

print("\n3. Testing get_recent_transactions()...")
transactions = get_recent_transactions(user_id, limit=10)
print(f"   ✓ Found {len(transactions)} transactions")
if transactions:
    print("   First 3 transactions:")
    for i, txn in enumerate(transactions[:3], 1):
        print(f"      {i}. {txn['date']} - {txn['description']} ({txn['category']}) - ₹{txn['amount']:.2f}")

print("\n4. Testing get_category_breakdown()...")
categories = get_category_breakdown(user_id)
print(f"   ✓ Found {len(categories)} categories")
if categories:
    total_pct = sum(c['pct'] for c in categories)
    print(f"   ✓ Total percentage: {total_pct}% (should be 100)")
    print("   Category breakdown:")
    for cat in categories:
        print(f"      {cat['name']}: ₹{cat['amount']:.2f} ({cat['pct']}%)")

print("\n5. Testing edge case: User with no expenses...")
# Create a test by checking if user_id 999 exists (shouldn't)
summary_new = get_summary_stats(999)
print(f"   ✓ Total Spent: ₹{summary_new['total_spent']:.2f}")
print(f"   ✓ Transaction Count: {summary_new['transaction_count']}")
print(f"   ✓ Top Category: {summary_new['top_category']}")
transactions_new = get_recent_transactions(999)
print(f"   ✓ Transactions: {len(transactions_new)} (should be 0)")
categories_new = get_category_breakdown(999)
print(f"   ✓ Categories: {len(categories_new)} (should be 0)")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE!")
print("=" * 60)

# Verify expected values
print("\nExpected vs Actual (Demo User):")
expected_total = 6035.50
expected_count = 8
expected_top = "Shopping"

status = "✓" if abs(summary_stats['total_spent'] - expected_total) < 0.01 else "✗"
print(f"{status} Total: Expected ₹{expected_total:.2f}, Got ₹{summary_stats['total_spent']:.2f}")

status = "✓" if summary_stats['transaction_count'] == expected_count else "✗"
print(f"{status} Count: Expected {expected_count}, Got {summary_stats['transaction_count']}")

status = "✓" if summary_stats['top_category'] == expected_top else "✗"
print(f"{status} Top Category: Expected '{expected_top}', Got '{summary_stats['top_category']}'")

status = "✓" if total_pct == 100 else "✗"
print(f"{status} Percentage Sum: Expected 100%, Got {total_pct}%")
