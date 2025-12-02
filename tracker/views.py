import os
import pandas as pd
from datetime import date, datetime, timedelta
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import UserProfile, TimeEntry
from .petLogic import *

CSV_PATH = os.path.join(settings.BASE_DIR, 'tracker', 'usage_data.csv')

from django.contrib.auth.decorators import login_required


# --- Helper: Calculate dopamine pet status ---
def get_pet_stats(request):
    """Unified logic for dopamine pet display and progress calculation."""
    focus_platform = request.session.get("focus_platform", None)
    points = request.session.get("points", 0)
    daily_avg = 0

    # Ensure CSV exists with correct columns
    if not os.path.exists(CSV_PATH):
        pd.DataFrame(columns=['Code', 'Date', 'Platform', 'Minutes']).to_csv(CSV_PATH, index=False)

    df = pd.read_csv(CSV_PATH)
    if "Code" not in df.columns:
        df["Code"] = ""  # default empty
        df.to_csv(CSV_PATH, index=False)
    # Get current user's share code
    profile = UserProfile.objects.get(user=request.user)
    share_code = profile.share_code

    # Filter CSV to only this user's entries
    df = df[df["Code"] == share_code]

    if not df.empty and "Platform" in df.columns and focus_platform:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        today = pd.to_datetime(date.today(), errors="coerce")
        yesterday = pd.to_datetime(date.today() - timedelta(days=1), errors="coerce")
        one_week_ago = datetime.now() - timedelta(days=7)
        recent = df[df["Date"] >= one_week_ago]
        focus_df = recent[recent["Platform"] == focus_platform]

        if not focus_df.empty:
            yesterday_total = focus_df[focus_df["Date"] == yesterday]["Minutes"].sum()
            today_total = focus_df[focus_df["Date"] == today]["Minutes"].sum()
            daily_avg = focus_df.groupby("Date")["Minutes"].sum().mean()

            # Award points if today's total is under yesterday's
            points = daily_point_change(today_total, yesterday_total, points)
            request.session["points"] = points
            request.session.modified = True


    # Evolution logic
    pet_image, evolution_stage, progress = return_pet_info(1, points)

    return {
        "focus_platform": focus_platform,
        "daily_avg": round(daily_avg, 2),
        "points": points,
        "evolution_stage": evolution_stage,
        "progress": progress,
        "pet_image": pet_image,
    }



@login_required(login_url='/accounts/login/')
def home(request):
    """Home page — same pet state as stats."""
    message = None
    focus_message = None

    # Ensure CSV exists
    if not os.path.exists(CSV_PATH):
        pd.DataFrame(columns=['Code', 'Date', 'Platform', 'Minutes']).to_csv(CSV_PATH, index=False)

    if request.method == "POST":

        # ----- SET FOCUS -----
        if 'set_focus' in request.POST:
            focus_platform = request.POST.get("focus_platform")
            if focus_platform:
                request.session["focus_platform"] = focus_platform
                focus_message = f"Focus platform set to {focus_platform}!"
            else:
                focus_message = "No focus platform selected."

        # ----- ADD USAGE ENTRY -----
        elif 'add_entry' in request.POST:
            platform = request.POST.get("platform")
            minutes = request.POST.get("minutes")
            date_input = request.POST.get("date")

            if not date_input:
                date_input =  date.today().isoformat()

            if platform and minutes:
                df = pd.read_csv(CSV_PATH)
                if "Code" not in df.columns:
                    df["Code"] = ""  # default empty
                    df.to_csv(CSV_PATH, index=False)

                # Get current user's share code
                profile = UserProfile.objects.get(user=request.user)
                share_code = profile.share_code

                new_row = {
                    "Code": share_code,
                    "Date": date_input,
                    "Platform": platform,
                    "Minutes": int(minutes)
                }

                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(CSV_PATH, index=False)

                message = f"Added {minutes} minutes for {platform}!"


    pet_stats = get_pet_stats(request)
    print(pet_stats)
    return render(request, "tracker/home.html", {**pet_stats, "message": message, "focus_message": focus_message})




@login_required(login_url='/accounts/login/')
def stats(request):
    """Stats page — displays usage summaries and dopamine pet info."""
    pet_stats = get_pet_stats(request)

    # --- Load usage data for summary cards ---
    total_minutes, most_used, avg_daily = 0, "N/A", 0

    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)

        # Filter to current user's data
        profile = UserProfile.objects.get(user=request.user)
        share_code = profile.share_code
        df = df[df["Code"] == share_code]

        if not df.empty:
            df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce").fillna(0)

            total_minutes = int(df["Minutes"].sum())
            avg_daily = round(df.groupby("Date")["Minutes"].sum().mean(), 2)

            if "Platform" in df.columns:
                most_used = df.groupby("Platform")["Minutes"].sum().idxmax()

        # ----- CHART DATA -----
    platform_labels = []
    platform_values = []
    weekly_labels = []
    weekly_values = []

    if not df.empty:

        # --- Time Spent per Platform Data ---
        platform_group = df.groupby("Platform")["Minutes"].sum()
        platform_labels = list(platform_group.index)
        platform_values = list(platform_group.values)

        # --- Weekly Trend (last 7 days) ---
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        week_ago = datetime.now() - timedelta(days=7)
        week_df = df[df["Date"] >= week_ago]

        if not week_df.empty:
            daily_totals = week_df.groupby(df["Date"].dt.date)["Minutes"].sum()
            weekly_labels = [str(d) for d in daily_totals.index]
            weekly_values = list(daily_totals.values)

    context = {
        **pet_stats,
        "total_minutes": total_minutes,
        "most_used": most_used,
        "avg_daily": avg_daily,
        "platform_labels": platform_labels,
        "platform_values": platform_values,
        "weekly_labels": weekly_labels,
        "weekly_values": weekly_values,
    }

    return render(request, "tracker/stats.html", context)



# ---------- LEADERBOARD PAGE ----------
@login_required(login_url='/accounts/login/')
def leaderboard(request):
    import os
    import pandas as pd
    from django.conf import settings

    csv_path = CSV_PATH

    try:
        # Try reading CSV safely
        if os.path.getsize(csv_path) == 0:
            raise pd.errors.EmptyDataError("CSV is empty")

        df = pd.read_csv(csv_path)

        if df.empty:
            leaderboard = []

        else:
            # Leaderboard: rank users by total minutes
            leaderboard_data = (
                df.groupby('Code', as_index=False)['Minutes']
                .sum()
                .sort_values('Minutes', ascending=True)
                .reset_index(drop=True)
            )

            leaderboard_data['Rank'] = leaderboard_data.index + 1
            leaderboard = leaderboard_data.to_dict(orient='records')

    except (FileNotFoundError, pd.errors.EmptyDataError):
        leaderboard = []

    return render(request, 'tracker/leaderboard.html', {'leaderboard': leaderboard})


# ---------- RESOURCES PAGE ----------
@login_required(login_url='/accounts/login/')
def resources(request):
    most_used = "N/A"
    platform_minutes = {}
    all_equal = False

    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        if not df.empty and "Minutes" in df.columns:
            if "Platform" in df.columns and not df["Platform"].empty:
                most_used = df.groupby("Platform")["Minutes"].sum().idxmax()
                platform_minutes = (
                    df.groupby("Platform")["Minutes"]
                    .sum()
                    .sort_values(ascending=False)
                    .to_dict()
                )

                non_other_vals = [v for k, v in platform_minutes.items() if str(k).strip().lower() != "other"]
                all_equal = len(non_other_vals) >= 2 and len(set(non_other_vals)) == 1

    context = {
        "most_used": most_used,
        "all_equal": all_equal,
    }

    return render(request, "tracker/resources.html", context)


def track_user(request):
    context = {}
    share_code = request.GET.get("code", "").strip().upper()

    if share_code:
        try:
            profile = UserProfile.objects.get(share_code=share_code)
            target_user = profile.user

            entries = TimeEntry.objects.filter(user=target_user).order_by('-date')

            total_minutes = sum(e.minutes for e in entries)

            context.update({
                "found": True,
                "target_user": target_user,
                "entries": entries,
                "total_minutes": total_minutes,
            })

        except UserProfile.DoesNotExist:
            context["error"] = "No user found with that share code."

    return render(request, "tracker/track_user.html", context)