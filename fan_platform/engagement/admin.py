from django.contrib import admin
from django import forms
from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponseRedirect
# Import Django admin, forms, and URL utilities
from .models import Club, UserProfile, ClubStats, Topic, Comment, Prediction, NewsArticle, NewsComment, Fixture
# Import app models

# Custom form for start_simulation action
class StartSimulationForm(forms.Form):
    # Form for setting simulation result
    final_result = forms.CharField(
        label="Final Result",
        help_text="Enter the score in x-y format (e.g., 2-1)",
        required=True
    )

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    # Admin config for NewsArticle
    list_display = ('title', 'club', 'published_date')
    # Columns in admin list view
    fields = ('club', 'title', 'summary', 'content', 'image', 'created_by')
    # Fields in admin edit form

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    # Admin config for Prediction
    list_display = ('user_profile', 'fixture_id', 'text', 'created_at', 'submission_count', 'is_correct')
    # Columns in admin list view
    list_filter = ('is_correct', 'created_at')
    # Filters for admin list
    search_fields = ('text', 'user_profile__user__username')
    # Searchable fields
    fields = ('user_profile', 'fixture_id', 'text', 'club', 'created_at', 'submission_count', 'is_correct', 'verified_at')
    # Fields in admin edit form

    def save_model(self, request, obj, form, change):
        # Update correct predictions on save
        super().save_model(request, obj, form, change)
        if 'is_correct' in form.changed_data and obj.is_correct:
            obj.user_profile.correct_predictions += 1
            obj.user_profile.check_challenge_completion()
            obj.user_profile.save()
            points_awarded = obj.user_profile.check_challenge_completion()
            if points_awarded > 0:
                self.message_user(request, f"Awarded {points_awarded} points for completing a challenge!")

    def delete_model(self, request, obj):
        # Adjust correct predictions on delete
        if obj.is_correct:
            obj.user_profile.correct_predictions -= 1
            obj.user_profile.check_challenge_completion()
            obj.user_profile.save()
        super().delete_model(request, obj)

@admin.register(Fixture)
class FixtureAdmin(admin.ModelAdmin):
    # Admin config for Fixture
    list_display = ('club', 'opponent', 'date', 'time', 'is_live', 'final_result')
    # Columns in admin list view
    fields = ('club', 'opponent', 'date', 'time', 'is_live', 'final_result')
    # Fields in admin edit form
    actions = ['start_simulation_action']
    # Custom admin action

    def start_simulation_action(self, request, queryset):
        # Action to start simulation
        print("Entered start_simulation_action")
        if queryset.count() != 1:
            self.message_user(request, "Please select a single fixture to start the simulation.")
            return
        fixture = queryset.first()
        if fixture.is_live:
            self.message_user(request, "This fixture is already live.")
            return
        return HttpResponseRedirect(f"/admin/engagement/fixture/{fixture.id}/start-simulation/")
    start_simulation_action.short_description = "Start simulation with final result"

    def get_urls(self):
        # Add custom URL for simulation
        urls = super().get_urls()
        custom_urls = [
            path('<int:fixture_id>/start-simulation/', self.admin_site.admin_view(self.start_simulation_view))
        ]
        return custom_urls + urls

    def start_simulation_view(self, request, fixture_id):
        # View for starting simulation
        print("Entered start_simulation_view")
        fixture = self.model.objects.get(id=fixture_id)
        if request.method == 'POST':
            print("Form submitted, full request.POST:", request.POST)
            form = StartSimulationForm(request.POST)
            if form.is_valid():
                print("Form is valid")
                result = form.cleaned_data['final_result']
                print(f"Extracted valid result: '{result}'")
                if '-' in result:
                    print(f"Valid result detected: {result}")
                    fixture.is_live = True
                    fixture.final_result = result
                    fixture.save()
                    print(f"Fixture saved: is_live={fixture.is_live}, final_result={fixture.final_result}")
                    self.message_user(request, f"Simulation started for {fixture.club.name} vs {fixture.opponent} with final result {result}.")
                    return redirect('/admin/engagement/fixture/')
                else:
                    print(f"Invalid result format: {result}")
                    self.message_user(request, "Invalid result format. Use x-y (e.g., 2-1).", level='error')
            else:
                print("Form is invalid, errors:", form.errors)
                self.message_user(request, "Invalid form data. Please enter a valid score.", level='error')
        else:
            form = StartSimulationForm()
        return render(
            request,
            'engagement/fixtures/start_simulation.html',
            {'fixture': fixture, 'form': form}
        )

    def set_final_result(self, request, queryset):
        # Action to set final result
        if 'apply' in request.POST:
            print("Form submitted for set_final_result, processing request.POST:", request.POST)
            selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
            queryset = self.model.objects.filter(id__in=selected)
        if queryset.count() != 1:
            self.message_user(request, "Please select a single fixture to set the final result.")
            return
        fixture = queryset.first()
        if fixture.is_live:
            self.message_user(request, "Cannot set final result while simulation is live. Stop the simulation first.")
            return
        result = request.POST.get('final_result', '')
        if result and '-' in result:
            fixture.final_result = result
            fixture.save()
            predictions = Prediction.objects.filter(fixture_id=fixture.id)
            for prediction in predictions:
                prediction.save()  # Triggers is_correct update
            self.message_user(request, f"Final result set to {result} for {fixture.club.name} vs {fixture.opponent}.")
        else:
            self.message_user(request, "Invalid result format. Use x-y (e.g., 2-1).", level='error')
    set_final_result.short_description = "Set final result"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        # Add final result form to change view
        extra_context = extra_context or {}
        extra_context['show_final_result_form'] = True
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def response_change(self, request, obj):
        # Handle final result submission
        if '_set_final_result' in request.POST:
            self.set_final_result(request, [obj])
            return self.response_change(request, obj)
        return super().response_change(request, obj)

# Register other models
admin.site.register(Club)
admin.site.register(UserProfile)
admin.site.register(ClubStats)
admin.site.register(Topic)
admin.site.register(Comment)
admin.site.register(NewsComment)