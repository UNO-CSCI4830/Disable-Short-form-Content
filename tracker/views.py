import os
import pandas as pd
from datetime import date, datetime, timedelta
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import UserProfile, TimeEntry
from django.shortcuts import render, get_object_or_404

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

        one_week_ago = datetime.now() - timedelta(days=7)
        recent = df[df["Date"] >= one_week_ago]
        focus_df = recent[recent["Platform"] == focus_platform]

        if not focus_df.empty:
            daily_avg = focus_df.groupby("Date")["Minutes"].sum().mean()

            # Award points if average < 60 min/day
            if daily_avg < 60:
                points += 10
                request.session["points"] = points
                request.session.modified = True

    # Evolution logic
    if points >= 100:
        pet_image = "tracker/assets/dragon_pet_final.png"
        evolution_stage = "Final Evolution 🐉"
        progress = 100

    elif points >= 40:
        pet_image = "tracker/assets/dragon_pet_adult.png"
        evolution_stage = "Stage 3 Evolution"
        progress = ((points - 40) / 60) * 100

    elif points >= 20:
        pet_image = "tracker/assets/dragon_pet_teen.png"
        evolution_stage = "Stage 2 Evolution"
        progress = ((points - 20) / 20) * 100

    else:
        pet_image = "tracker/assets/dragon_pet_egg.png"
        evolution_stage = "Baby Dragon 🐣"
        progress = (points / 20) * 100

    return {
        "focus_platform": focus_platform,
        "daily_avg": round(daily_avg, 2),
        "points": points,
        "evolution_stage": evolution_stage,
        "progress": round(progress, 2),
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
                    "Date": date.today().isoformat(),
                    "Platform": platform,
                    "Minutes": int(minutes)
                }

                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(CSV_PATH, index=False)

                message = f"Added {minutes} minutes for {platform}!"

    pet_stats = get_pet_stats(request)
    return render(request, "tracker/home.html", {**pet_stats, "message": message, "focus_message": focus_message})




@login_required(login_url='/accounts/login/')
def stats(request):
    """Stats page — displays usage summaries and dopamine pet info."""
    pet_stats = get_pet_stats(request)

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

    context = {
        **pet_stats,
        "total_minutes": total_minutes,
        "most_used": most_used,
        "avg_daily": avg_daily,
    }

    return render(request, "tracker/stats.html", context)



# ---------- LEADERBOARD PAGE ----------
@login_required(login_url='/accounts/login/')
def leaderboard(request):
    import pandas as pd

    csv_path = CSV_PATH

    try:
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




def track_user(request):
    context = {}
    share_code = request.GET.get("code", "").strip().upper()

    if share_code:
        try:
            profile = UserProfile.objects.get(share_code=share_code)
            target_user = profile.user

            entries = TimeEntry.objects.filter(user=target_user).order_by('-date')
            total_minutes = sum(e.minutes for e in entries)

            context["user_data"] = {
                "share_code": share_code,         # ← FIX
                "total_minutes": total_minutes,
                "top_platform": "N/A",
                "pet_mood": "Happy",
            }

        except UserProfile.DoesNotExist:
            context["error"] = "No user found with that share code."

    return render(request, "tracker/track_user.html", context)

def track_user_detail(request, share_code):
    """Show detailed stats for a user based on their share code."""
    share_code = share_code.strip().upper()
    profile = get_object_or_404(UserProfile, share_code=share_code)
    target_user = profile.user

    entries = TimeEntry.objects.filter(user=target_user).order_by('-date')
    total_minutes = sum(e.minutes for e in entries)

    context = {
        "target_user": target_user,
        "entries": entries,
        "total_minutes": total_minutes,
    }

    return render(request, "tracker/track_user_detail.html", context)