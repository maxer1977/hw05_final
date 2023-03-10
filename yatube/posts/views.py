from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow

PAGE: int = 10


def paginator(request, post_list):
    """Paginator для шаблонов"""
    paginator = Paginator(post_list, PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(timeout=20, key_prefix='index_page')
def index(request):
    """Главная страница со всеми записями"""
    post_list = Post.objects.select_related('author', 'group').order_by(
        '-pub_date')
    context = {'page_obj': paginator(request, post_list), }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Страница с записями одной группы"""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author', 'group').order_by(
        '-pub_date')
    context = {
        'group': group,
        'page_obj': paginator(request, post_list),
    }
    template = 'posts/group_list.html'
    return render(request, template, context)


def profile(request, username):
    """Страница с записями одного автора"""
    user = get_object_or_404(User, username=username)
    following = (request.user.is_authenticated and Follow.objects.filter(
        author=user, user=request.user).exists())
    post_list = user.posts.select_related('author', 'group').order_by(
        '-pub_date')
    context = {'author': user, 'page_obj': paginator(request, post_list),
               'following': following, }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница с одной записью"""
    post = get_object_or_404(Post, id=post_id)
    count_posts = post.author.posts.count
    comments = post.comments.select_related('author', 'post').order_by(
        '-created')
    form = PostForm()
    comment_form = CommentForm()
    context = {'post': post, 'count_posts': count_posts, 'comments': comments,
               'form': form, 'comment_form': comment_form}
    return render(request, 'posts/post_detail.html', context)


@csrf_exempt
@login_required
def post_create(request):
    """Страница с формой для создания новой записи"""
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)
    return render(request, 'posts/create_post.html', {'form': form})


@csrf_exempt
@login_required
def post_edit(request, post_id):
    """Страница с формой для редактирования записи"""
    is_edit = True
    post_to_edit = get_object_or_404(Post, id=post_id)
    if post_to_edit.author == request.user:
        form = PostForm(request.POST or None,
                        files=request.FILES or None,
                        instance=post_to_edit)
        if form.is_valid():
            form = form.save()
            return redirect('posts:post_detail', post_id)
        return render(request, 'posts/create_post.html',
                      {'is_edit': is_edit, 'form': form})
    return redirect('posts:post_detail', post_id)


@csrf_exempt
@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@csrf_exempt
@login_required
def follow_index(request):
    """Список записей от авторов по подписке"""
    user = request.user
    authors_list = Follow.objects.filter(user=user).values_list('author_id',
                                                                flat=True)
    post_list = Post.objects.select_related(
        'author', 'group').filter(author__in=authors_list)
    context = {'page_obj': paginator(request, post_list), 'user': user}
    return render(request, 'posts/follow.html', context)


@csrf_exempt
@login_required
def profile_follow(request, username):
    """Подписаться на автора"""
    author = get_object_or_404(User, username=username)
    if request.user != author and not Follow.objects.filter(
            user=request.user, author=author).exists():
        Follow.objects.create(
            user=request.user,
            author=author)
        return redirect('posts:follow_index', )
    return redirect('posts:profile', username=author.username)


@csrf_exempt
@login_required
def profile_unfollow(request, username):
    """Отписаться от автора"""
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user=request.user,
        author=author).delete()

    return redirect('posts:follow_index', )
