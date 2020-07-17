from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.cache import cache_page


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )

def server_error(request):
    return render(request, "misc/500.html", status=500)


def index(request):
    post_list = Post.objects.order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )

def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group).all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        "group.html",
        {"group": group, "posts": posts, 'page': page, 'paginator': paginator})

@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
    else:
        form = PostForm()
    return render(request, 'new.html', {'form': form, 'is_edit': False})

@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = False
    if Follow.objects.filter(user=request.user, author=user):
        following = True
    return render(
        request,
        'profile.html',
        {'page': page, 'paginator': paginator, 'profile': user, "following": following, "count_post": paginator.count})

def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    comment = Comment.objects.filter(post=post_id)
    return render(
        request,
        'post.html',
        {'post': post, 'author': post.author, 'comments': comment, 'form': form}
    )

@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    if request.user != post.author:
        return redirect('post', username=request.user.username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username=request.user.username, post_id=post_id)
    return render(request, 'new.html', {'form': form, 'post': post, 'is_edit': True})

@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.post = post
        form.save()
        return redirect(reverse("post", kwargs={'username': username, 'post_id': post_id}))
    return redirect(reverse("post", kwargs={'username': username, 'post_id': post_id}))

@login_required
def follow_index(request):
    post_list = Post.objects.select_related('author').filter(author__following__user=request.user)
    #post_list = Post.objects.order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return redirect(
        'follow.html'
        )

@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    obj_exists = Follow.objects.filter(user=request.user, author=author).exists()
    if not obj_exists and author.id != request.user.id:
        new = Follow(user=request.user, author=author)
        new.save()
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    follow = get_object_or_404(User, username=username)
    Follow.objects.filter(author=follow).delete()
    return redirect(reverse("profile", kwargs={'username': username}))