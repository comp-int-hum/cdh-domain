from guardian.shortcuts import get_objects_for_user
from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from turkle.models import TaskAssignment, Batch, Project

from django.views.generic.list import ListView

@login_required(login_url="/accounts/login/")
def index(request):
    """
    Security behavior:
    - Anyone can access the page, but the page only shows the user
      information they have access to.
    """
    if request.method == "POST" and request.user.is_authenticated:
        action = request.POST["action"][0]
        if action == "change_project":
            
            pass
        elif action == "add_project":
            pass
        elif action == "add_batch":
            pass
        elif action == "delete_project":
            pass
        elif action == "delete_batch":
            pass
        print(request, request.POST, request.headers)
    abandoned_assignments = []
    owned_projects = []
    if request.user.is_authenticated:
        for ha in TaskAssignment.objects.filter(assigned_to=request.user)\
                                        .filter(completed=False)\
                                        .filter(task__batch__active=True)\
                                        .filter(task__batch__project__active=True):
            abandoned_assignments.append({
                'task': ha.task,
                'task_assignment_id': ha.id
            })
    accordion = {
        "subitems" : [
            {
                "name" : proj.name,
                "form" : forms.ProjectForm(instance=proj),
                "empty_form" : forms.BatchForm(initial={"created_by" : request.user}),
                "subitems_title" : "Batches",
                "subitems" : [
                    {
                        "name" : b.name,
                        "form" : forms.BatchForm(instance=b),
                    } for b in Batch.objects.filter(project=proj)
                ],
            } for proj in get_objects_for_user(request.user, "turkle.view_project")
        ],
        "empty_form" : forms.ProjectForm(),
    }
    #owned_projects = forms.ProjectFormset(queryset=get_objects_for_user(request.user, "turkle.view_project"))
    #owned_projects = [(p.name, forms.ProjectForm(instance=p), [(b.name, forms.BatchForm(instance=b)) for b in Batch.objects.filter(project=p)] + [("Create a new batch", forms.BatchForm(initial={"created_by" : request.user, "project" : p.id}))]) for p in get_objects_for_user(request.user, "turkle.view_project")] + [("Create a new project", forms.ProjectForm(initial={"created_by" : request.user}), [])]
    batch_list = Batch.access_permitted_for(request.user)
    batch_query = Batch.objects.filter(id__in=[b.id for b in batch_list])

    available_task_counts = Batch.available_task_counts_for(batch_query, request.user)

    batch_rows = []
    for batch in batch_query.values('created_at', 'id', 'name', 'project__name'):
        total_tasks_available = available_task_counts[batch['id']]

        if total_tasks_available > 0:
            batch_rows.append({
                'project_name': batch['project__name'],
                'batch_name': batch['name'],
                'batch_published': batch['created_at'],
                'assignments_available': total_tasks_available,
                'preview_next_task_url': reverse('preview_next_task',
                                                 kwargs={'batch_id': batch['id']}),
                'accept_next_task_url': reverse('accept_next_task',
                                                kwargs={'batch_id': batch['id']})
            })
    return render(request, 'turkle/index.html', {
        'abandoned_assignments': abandoned_assignments,
        'batch_rows': batch_rows,
        #"owned_projects" : owned_projects,
        "accordion" : accordion,
        "empty_form" : forms.ProjectForm(),
    })


