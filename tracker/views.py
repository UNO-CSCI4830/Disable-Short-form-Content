import os
import pandas as pd
from datetime import date
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# ---------- HOME PAGE ----------
@login_required(login_url='/accounts/login/')
def home(request):
    # Confirmed file path
    csv_path = os.path.join(settings.BASE_DIR, 'tracker', 'usage_data.csv')

    # Ensure CSV file exists with headers
    if not os.path.exists(csv_path):
        pd.DataFrame(columns=['Date', 'Platform', 'Minutes']).to_csv(csv_path, index=False)

    if request.method == 'POST':
        platform = request.POST.get('platform')
        minutes = request.POST.get('minutes')

        print(f"Received POST data: Platform={platform}, Minutes={minutes}")  # debug line
        print(f"Writing to: {csv_path}")  # debug line

        if platform and minutes:
            new_row = {
                'Date': date.today().isoformat(),
                'Platform': platform,
                'Minutes': int(minutes)
            }

            try:
                df = pd.DataFrame([new_row])
                df.to_csv(csv_path, mode='a', header=False, index=False)
                print("Successfully wrote to CSV file.")
            except Exception as e:
                print(f"Error writing CSV: {e}")

            return render(request, 'tracker/home.html', {
                'message': f"Added {minutes} minutes for {platform}!"
            })

    # Default: GET request
    return render(request, 'tracker/home.html')


# ---------- STATS PAGE ----------
@login_required(login_url='/accounts/login/')
def stats(request):
    csv_path = os.path.join(settings.BASE_DIR, 'tracker', 'usage_data.csv')

    # If CSV missing or empty, show default placeholders
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        context = {
            'total_minutes': 0,
            'most_used': "N/A",
            'avg_daily': 0,
            'chart_labels': [],
            'chart_values': [],
        }
        return render(request, 'tracker/stats.html', context)

    try:
        # Read CSV safely
        df = pd.read_csv(csv_path)

        # Fix missing headers if needed
        expected_cols = ['Date', 'Platform', 'Minutes']
        if list(df.columns) != expected_cols:
            df.columns = expected_cols[:len(df.columns)]

        # --- Stats Calculations ---
        total_minutes = df['Minutes'].sum()
        most_used = (
            df.groupby('Platform')['Minutes']
              .sum()
              .sort_values(ascending=False)
              .idxmax()
        )
        avg_daily = round(df.groupby('Date')['Minutes'].sum().mean(), 1)

        # --- Chart Data ---
        totals = df.groupby('Platform')['Minutes'].sum().sort_values(ascending=False)
        chart_labels = list(totals.index)
        chart_values = list(totals.values)

        context = {
            'total_minutes': total_minutes,
            'most_used': most_used,
            'avg_daily': avg_daily,
            'chart_labels': chart_labels,
            'chart_values': chart_values,
        }

    except Exception as e:
        print(f"Error generating stats: {e}")
        context = {
            'total_minutes': 0,
            'most_used': "N/A",
            'avg_daily': 0,
            'chart_labels': [],
            'chart_values': [],
        }

    return render(request, 'tracker/stats.html', context)



# ---------- LEADERBOARD PAGE ----------
@login_required(login_url='/accounts/login/')
def leaderboard(request):
    import os
    import pandas as pd
    from django.conf import settings

    csv_path = os.path.join(settings.BASE_DIR, 'tracker', 'usage_data.csv')

    try:
        # Try reading CSV safely
        if os.path.getsize(csv_path) == 0:
            raise pd.errors.EmptyDataError("CSV is empty")

        df = pd.read_csv(csv_path)

        if df.empty:
            leaderboard = []
        else:
            # Group and rank data
            leaderboard_data = (
                df.groupby('Platform', as_index=False)['Minutes']
                .sum()
                .sort_values('Minutes', ascending=True)
                .reset_index(drop=True)
            )
            leaderboard_data['Rank'] = leaderboard_data.index + 1
            leaderboard = leaderboard_data.to_dict(orient='records')

    except (FileNotFoundError, pd.errors.EmptyDataError):
        leaderboard = []

    return render(request, 'tracker/leaderboard.html', {'leaderboard': leaderboard})

