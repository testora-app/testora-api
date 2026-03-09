# Project Name
> This is a template for starting a flask application. The basics have been set up.


## Setup
Clone this project.

Run `pip install -r requiremnts.txt`

## DB migrations
After changes are made to the models run

`flask db migrate -m "{enter describe meessage here}"`
to generate the migrations file.

The app runs migrations automatically when it starts up.

## Usage

To run the app and check if everything is working correctly


Start the server with this command
`python run.py`

Start the shell with the app context with

`python run.py shell`

## Unit Tests
There is a test module set up for the application already using pytest

To run the tests, run this in the console
`python -m pytest tests`

## Subscription System

### Overview
The Preppee subscription system implements a seat-based SaaS billing model for schools with flexible billing cycles and trial periods.

### Tiers

#### Trial Tier
- **Duration**: 30 days
- **Seats**: 100 students
- **Features**: All premium features enabled
- **Pricing**: Free
- **Behavior**:
  - New schools automatically start on trial
  - Auto-downgrades to Free tier after 30 days if not upgraded
  - Email notification sent if school has > 10 students when trial expires

#### Free Tier
- **Seats**: 10 students
- **Features**: Basic features only
- **Pricing**: Free
- **Limitations**:
  - No exam mode
  - Limited subjects for BECE
  - Test history limited to 10

#### Premium Tier
- **Seats**: Flexible (purchased by school)
- **Features**: All premium features
- **Pricing**: Seat-based with billing cycles
  - Monthly: GH₵75/seat
  - Termly: GH₵210/seat
  - Yearly: GH₵600/seat
- **Capabilities**:
  - Add seats mid-cycle (prorated payment)
  - Schedule seat reduction at renewal
  - Switch billing cycles at renewal
  - Schedule downgrade to Free

#### Premium Plus Tier
- **Status**: Coming Soon
- Currently not available for purchase

### Key Features

#### 1. Trial to Paid Conversion
Schools on trial can upgrade to Premium at any time by:
1. Selecting number of seats needed
2. Choosing billing cycle (monthly/termly/yearly)
3. Completing payment via Paystack
4. Trial period ends immediately upon upgrade

#### 2. Billing Cycle Switching
Premium schools can schedule billing cycle changes:
- Changes take effect at next renewal date
- New price per seat calculated automatically
- Cannot switch if downgrade is scheduled
- No mid-cycle refunds

**API Endpoints:**
- `POST /subscriptions/schedule-cycle-change` - Schedule cycle change
- `DELETE /subscriptions/schedule-cycle-change` - Cancel scheduled change

**Request Format:**
```json
{
  "data": {
    "new_cycle": "monthly" | "termly" | "yearly"
  }
}
```

#### 3. Seat Management
Schools can manage their seat allocation:
- **Add Seats**: Immediate effect with prorated payment
- **Reduce Seats**: Scheduled for next renewal (no mid-term refunds)
- **Restrictions**: Cannot change seats when downgrade is scheduled

#### 4. Downgrade to Free
Schools can schedule downgrade to Free tier:
- Takes effect at renewal date
- Reduces seats to 10
- Disables premium features
- Email sent if school has > 10 students after downgrade

#### 5. Email Notifications
Automated emails sent for:
- Trial expiry with student count warning
- Scheduled downgrade confirmation
- Billing cycle change confirmation

### Database Schema

**School Model Fields:**
```python
subscription_tier               # trial | free | premium | premium_plus
billing_cycle                   # monthly | termly | yearly (null for trial/free)
total_seats                     # Number of purchased seats
price_per_seat                  # Current price per seat
subscription_expiry_date        # Next renewal date
scheduled_seat_reduction        # Seats to remove at renewal
scheduled_reduction_date        # When reduction takes effect
scheduled_downgrade             # Boolean flag for downgrade
scheduled_downgrade_date        # When downgrade takes effect
scheduled_billing_cycle         # New cycle to switch to
scheduled_billing_cycle_date    # When cycle change takes effect
```

### API Endpoints

All subscription endpoints require `UserTypes.school_admin` authentication.

#### Get Current Plan
```
GET /subscriptions/current
```
Returns current subscription details including all scheduled changes.

#### Add Seats
```
POST /subscriptions/add-seats
Body: { "data": { "seats": number } }
```
Initiates Paystack payment for prorated seat addition.

#### Schedule Seat Reduction
```
POST /subscriptions/schedule-reduction
Body: { "data": { "seats": number } }
```
Schedules seat reduction for next renewal.

#### Schedule Downgrade
```
POST /subscriptions/schedule-downgrade
Body: { "data": { "confirmDowngrade": true } }
```
Schedules downgrade to Free tier.

#### Cancel Downgrade
```
DELETE /subscriptions/schedule-downgrade
```
Cancels scheduled downgrade.

#### Schedule Cycle Change
```
POST /subscriptions/schedule-cycle-change
Body: { "data": { "new_cycle": "monthly" | "termly" | "yearly" } }
```
Schedules billing cycle change for next renewal.

#### Cancel Cycle Change
```
DELETE /subscriptions/schedule-cycle-change
```
Cancels scheduled billing cycle change.

#### Cancel All Scheduled Changes
```
POST /subscriptions/cancel-scheduled-change
```
Cancels all scheduled seat reductions and downgrades.

### Renewal Process

The `/billing-process/` endpoint processes renewals:
1. **Trial Expiry** (highest priority)
   - Downgrades trial schools to Free
   - Sets seats to 10
   - Sends email if > 10 students

2. **Scheduled Downgrade**
   - Downgrades to Free tier
   - Clears all scheduled changes
   - Sends email if > 10 students

3. **Billing Cycle Change**
   - Applies new billing cycle
   - Updates price_per_seat
   - Clears scheduled cycle change

4. **Seat Reduction**
   - Reduces total_seats
   - Clears scheduled reduction

**Note**: This endpoint must be called manually or via cron job with `?code=<APP_SECRET_KEY>`.

### Payment Flow

#### Subscription Payment
1. School initiates payment (add seats, upgrade from trial)
2. Backend creates billing history record with `payment_status=pending`
3. Paystack payment initialized, returns `authorization_url`
4. Frontend redirects to Paystack
5. Payment confirmed via `/payment/<reference>/confirm/`
6. Seats added to school, billing history updated

#### Payment Confirmation
- Paystack webhook: `POST /paystack-webhook/`
- Manual confirmation: `GET /payment/<reference>/confirm/`

Both update payment status and apply seat changes.

### Frontend Integration

**React Query Hooks:**
- `useQuery({ queryKey: ["subscription-current"] })` - Fetch current plan
- `useMutation({ mutationFn: scheduleCycleChange })` - Schedule cycle change
- `useMutation({ mutationFn: cancelScheduledCycleChange })` - Cancel cycle change

**Components:**
- `PlanSummaryCard` - Displays current plan with trial/cycle change indicators
- `ManagePlanModal` - Seat management and cycle switcher
- `DowngradeModal` - Downgrade confirmation with warnings
- `TierCard` - Displays available tiers

### Testing

Run subscription tests:
```bash
python -m pytest tests/test_subscriptions_routes.py -v
python -m pytest tests/test_subscription_manager.py -v
```

### Migration

To apply the trial tier and cycle switching migration:
```bash
flask db upgrade
```

This migration:
- Adds `scheduled_billing_cycle` and `scheduled_billing_cycle_date` columns
- Converts schools with 100,000+ seats to trial tier with 100 seats
- Leaves paid premium schools unchanged

### Known Limitations

1. **Manual Renewal**: `/billing-process/` must be called manually or via cron (not auto-scheduled)
2. **No Mid-Cycle Changes**: Cycle switches only at renewal (industry standard)
3. **No Proration on Downgrade**: Changes at renewal, no refunds (by design)
4. **Hardcoded Pricing**: Prices in constants (acceptable for 1 year fixed pricing)
5. **Email Delivery**: Depends on SMTP2GO service availability

## Conclusion
You can continue with your development after it runs successfully.

> NB: This template uses Flask Script, it is necessary to use Flask 1.1.2 to get the flask-script module to work.
> Using flask 2 will throw errors. Thanks.
> Enjoy!