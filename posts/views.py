from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator


def index(request):
    post_list = Post.objects.order_by("-pub_date").all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, "index.html", {
            'page': page, 'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, "group.html", {
            "group": group, 'page': page, 'paginator': paginator})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = False
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    if any(follow.user == request.user for follow in author.following.all()):
        following = True

    following_count = author.following.count()
    followers_count = author.follower.count()
    return render(request,
                  'profile.html',
                  {'author': author,
                   'page': page,
                   'paginator': paginator,
                   'following': following,
                   'following_count': following_count,
                   'followers_count': followers_count})


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    author = post.author
    posts = author.posts.count()
    comments = post.comments.all()
    form = CommentForm()

    following = False
    if any(follow.user == request.user for follow in author.following.all()):
        following = True
    following_count = author.following.count()
    followers_count = author.follower.count()

    return render(request,
                  'post.html',
                  {'author': author,
                   'posts': posts,
                   'post': post,
                   'comments': comments,
                   'form': form,
                   'following': following,
                   'following_count': following_count,
                   'followers_count': followers_count})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    author = post.author

    if request.user != author:
        return redirect('post', username=username, post_id=post_id)

    method = 'edit'

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            return redirect('post', username=username, post_id=post_id)

    return render(request,
                  'new.html',
                  {'form': form,
                   'post': post,
                   'method': method})


@login_required
def new_post(request):

    method = 'new'

    form = PostForm(request.POST or None, files=request.FILES)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            return redirect('index')

    return render(
        request, 'new.html', {
            'form': form, 'method': method})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('post', username=username, post_id=post_id)

    return render(
        request, 'comments.html', {'form': form})


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(
        author__in=request.user.follower.all().values('author'))
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, "follow.html", {
            'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user and not Follow.objects.filter(
            author__username=username, user=request.user).exists():
        Follow.objects.get_or_create(author=author, user=request.user)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        author__username=username,
        user=request.user).delete()
    return redirect('profile', username=username)
