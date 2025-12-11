import os
import pandas as pd
from datetime import date, datetime, timedelta
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import UserProfile, TimeEntry
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from .petLogic import *
# Double checked imports
CSV_PATH = os.path.join(settings.BASE_DIR, 'tracker', 'usage_data.csv')

from django.contrib.auth.decorators import login_required


# --- Helper: Calculate dopamine pet status ---
def get_pet_stats(request):
    """Unified logic for dopamine pet display and progress calculation."""
    focus_platform = request.session.get("focus_platform", None)
    points = request.session.get("points", 0)
    pet_type = request.session.get("pet_type", 1)
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


    # Evolution logic
    pet_image, evolution_stage, progress = return_pet_info(pet_type, points)

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
                # -------------------------------------------
                # REWARD LOGIC — ONLY RUNS WHEN CSV UPDATED
                DAILY_LIMIT = 15
                points = request.session.get("points", 0)

                # Calculate today's total usage (all platforms or only focus platform)
                today_total = df[
                    (df["Code"] == share_code) &
                    (df["Date"] == date_input)
                ]["Minutes"].sum()

                # Calculate yesterday's total
                yesterday_str = (date.fromisoformat(date_input) - timedelta(days=1)).isoformat()
                yesterday_total = df[
                    (df["Code"] == share_code) &
                    (df["Date"] == yesterday_str)
                ]["Minutes"].sum()

                # --- Condition 1: Daily limit rule
                if today_total <= DAILY_LIMIT:
                    points += 1

                # --- Condition 2: Improvement rule
                if today_total < yesterday_total:
                    points += 1

                # Save updated points
                request.session["points"] = points
                request.session.modified = True
                # -------------------------------------------
        elif 'set_pet' in request.POST:
            pet_type = int(request.POST.get("pet_type"))
            request.session["pet_type"] = pet_type
            request.session.modified = True
            message = f"Pet type set to {pet_type}!"

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
        platform_values = [float(v) for v in platform_group.values]

        # --- Weekly Trend (last 7 days) ---
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        week_ago = datetime.now() - timedelta(days=7)
        week_df = df[df["Date"] >= week_ago]

        if not week_df.empty:
            daily_totals = week_df.groupby(df["Date"].dt.date)["Minutes"].sum()
            weekly_labels = [str(d) for d in daily_totals.index]
            weekly_values = [float(v) for v in daily_totals.values]

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
    """
    GET ?code= -> redirect to detail
    POST (friend_code) -> add friend for logged-in user
    Renders search/add form with messages and current friends list.
    """
    context = {}
    # show current user's friends
    user_profile = get_object_or_404(UserProfile, user=request.user)
    context["friends"] = user_profile.friends.all()

    # Handle add-friend POST
    if request.method == "POST" and "friend_code" in request.POST:
        raw_code = request.POST.get("friend_code", "").strip()
        if not raw_code:
            context["error"] = "Please enter a code."
        else:
            code = raw_code.upper()
            # prevent adding yourself
            if code == user_profile.share_code:
                context["error"] = "You cannot add yourself as a friend."
            else:
                try:
                    target_profile = UserProfile.objects.get(share_code=code)
                    # add and save
                    user_profile.friends.add(target_profile)
                    # optional: ensure mutual friendship
                    # target_profile.friends.add(user_profile)
                    context["message"] = f"Added {target_profile.user.username} as a friend."
                    # refresh friends list
                    context["friends"] = user_profile.friends.all()
                except UserProfile.DoesNotExist:
                    context["error"] = "No account found with that code."

    # Handle code search (redirect to detail)
    share_code = request.GET.get("code", "").strip()
    if share_code:
        return redirect("track_user_detail", share_code=share_code.upper())

    return render(request, "tracker/track_user.html", context)
def track_user_detail(request, share_code):

    share_code = share_code.strip().upper()
    profile = get_object_or_404(UserProfile, share_code=share_code)
    target_user = profile.user

    # Ensure CSV exists; if not, return an empty result consistent with stats()
    if not os.path.exists(CSV_PATH):
        entries = []
        total_minutes = 0
        daily_avg = 0
        pet_mood = "N/A"
        most_used = "N/A"
        return render(request, "tracker/track_user_detail.html", {
            "target_user": target_user,
            "entries": entries,
            "total_minutes": total_minutes,
            "daily_avg": daily_avg,
            "pet_mood": pet_mood,
            "most_used": most_used,
        })


    df = pd.read_csv(CSV_PATH)


    if "Code" not in df.columns:
        df["Code"] = ""

    df_user = df[df["Code"].astype(str).str.upper() == share_code]

    if not df_user.empty:
        if "Minutes" in df_user.columns:
            df_user["Minutes"] = pd.to_numeric(df_user["Minutes"], errors="coerce").fillna(0).astype(int)
        else:
            df_user["Minutes"] = 0
        if "Date" in df_user.columns:
            df_user["Date"] = pd.to_datetime(df_user["Date"], errors="coerce").dt.date
        else:

            df_user["Date"] = pd.to_datetime("today").date()

        # total minutes (match stats)
        total_minutes = int(df_user["Minutes"].sum())

        try:
            daily_avg = round(df_user.groupby("Date")["Minutes"].sum().mean(), 2)
        except Exception:
            daily_avg = 0


        if "Platform" in df_user.columns and not df_user["Platform"].isnull().all():

            try:
                most_used = df_user.groupby("Platform")["Minutes"].sum().idxmax()
            except Exception:
                most_used = "N/A"
        else:
            most_used = "N/A"

        entries = [
            {
                "date": row["Date"].isoformat() if hasattr(row["Date"], "isoformat") else str(row["Date"]),
                "platform": (row["Platform"] if "Platform" in row and pd.notna(row["Platform"]) else "N/A"),
                "minutes": int(row["Minutes"])
            }
            for _, row in df_user.sort_values("Date", ascending=False).iterrows()
        ]

    else:
        entries = []
        total_minutes = 0
        daily_avg = 0
        most_used = "N/A"

    if daily_avg < 60 and daily_avg > 0:
        pet_mood = "Happy"
    elif daily_avg < 120 and daily_avg > 0:
        pet_mood = "Neutral"
    elif daily_avg == 0:
        pet_mood = "No Data"
    else:
        pet_mood = "Stressed"

    context = {
        "target_user": target_user,
        "entries": entries,
        "total_minutes": total_minutes,
        "daily_avg": daily_avg,
        "pet_mood": pet_mood,
        "most_used": most_used,
    }

    return render(request, "tracker/track_user_detail.html", context)

def friends_list(request):
    return render(request, "tracker/friends_list.html")
