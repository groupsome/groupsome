from django import template

register = template.Library()


def get_survey_user_voted_count(survey):
    users = []
    for choice in survey.choices.all():
        for vote in choice.votes.all():
            if vote.user not in users:
                users.append(vote.user)
    return len(users)


def get_survey_votes_count(survey):
    count = 0
    for choice in survey.choices.all():
        count += choice.votes.all().count()

    return count


def get_choice_votes(choice):
    return choice.votes.all().count()


def get_choice_percentage(choice):
    all_count = get_survey_votes_count(choice.survey)
    choice_count = choice.votes.all().count()
    try:
        return "%d%%" % (float(choice_count) / all_count * 100)
    except (ValueError, ZeroDivisionError):
        return "0%"


def get_user_voted(survey, request):

    for choice in survey.choices.all():
        voted = choice.votes.all().filter(user=request.user)
        if voted:
            return True

    return False


def get_user_voted_for_choice(choice, request):

    voted = choice.votes.all().filter(user=request.user)
    if voted:
        return True

    return False


def get_users_from_choice(choice):

    users = []
    for vote in choice.votes.all():
        if vote.user not in users:
            users.append(vote.user)
    return users


def get_user_is_admin_for_survey(survey, user):

    if user in survey.group.admins.all():
        return True

    return False

register.filter('survey_user_voted_count', get_survey_user_voted_count)
register.filter('survey_votes_count', get_survey_votes_count)
register.filter('choice_percentage', get_choice_percentage)
register.filter('user_voted', get_user_voted)
register.filter('user_voted_for_choice', get_user_voted_for_choice)
register.filter('choice_votes', get_choice_votes)
register.filter('users_from_choice', get_users_from_choice)
register.filter('user_is_admin_for_survey', get_user_is_admin_for_survey)
