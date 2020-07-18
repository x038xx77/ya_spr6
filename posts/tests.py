from django.test import TestCase, Client
from .models import Post, User, Group, Comment, Follow
from django.urls import reverse


class Profile_not_authTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user_to_follow = User.objects.create_user(username='test_user_to_follow', password=12345)

    def test_no_auth_user_publish_post_comment(self):
        response = self.client.get('/new/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')
        count = Post.objects.count()
        self.assertEqual(count, 0)

        comment_not_auth = self.client.get(reverse('add_comment',
                                                   kwargs={'username': self.user_to_follow.username, "post_id": '1'}))
        self.assertRedirects(comment_not_auth, '/auth/login/?next=/test_user_to_follow/1/comment')


class Profile_authTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.test_user = User.objects.create(username='TestUser', password='testPass')
        self.testgroup = Group.objects.create(slug="test74posts", title="Test Group1", description="Test Descr.")
        self.client.force_login(self.test_user)

    def check_post_variable(self, url, text, group, author):
        response = self.client.get(url, follow=True)
        paginator = response.context.get('paginator')
        if paginator is not None:
            post = response.context['page'][0]
            count = paginator.count
            self.assertEqual(count, 1)
        else:
            post = response.context['post']
        self.assertEqual(post.text, text)
        self.assertEqual(post.group, group)
        self.assertEqual(post.author, author)

    def test_personal_page_after_registration(self):
        response = self.client.get(reverse('profile', kwargs={'username': self.test_user.username}))
        self.assertEqual(response.status_code, 200)

    def test_Auth_publish_new_post(self):
        text_post = 'Example new post for test'
        self.client.post(reverse('new_post'), {'text': text_post, 'group': self.testgroup.id}, follow=True)
        self.assertEqual(Post.objects.count(), 1)
        newpost = Post.objects.first()
        self.assertEqual(newpost.text, text_post)
        self.assertEqual(newpost.author, self.test_user)
        self.assertEqual(newpost.group, self.testgroup)

    def test_posted_new_entry_all_page(self):
        text_test = 'Example text for test'
        post = Post.objects.create(author=self.test_user,
                                        text=text_test,
                                        group=self.testgroup)
        urls = [reverse('index'),
                reverse('profile',
                        kwargs={'username': self.test_user.username}),
                reverse('post',
                        kwargs={'username': self.test_user.username, 'post_id': post.id})]
        for url in urls:
            self.check_post_variable(url, text=text_test, group=self.testgroup, author=self.test_user)

    def test_posted_edited_page(self):
        text_test = 'Example text for test'
        text_edit = 'Example text edited for test'
        post = Post.objects.create(author=self.test_user,
                                   text=text_test,
                                   group=self.testgroup)
        group2 = Group.objects.create(slug="test75posts",
                                      title="Test Group2 New",
                                      description="Test Descr_group.")
        response = self.client.post(reverse('post_edit',
                                 kwargs={'username': self.test_user.username,
                                         'post_id': post.id}
                                 ),
                                 data={
                                     'group': group2.id,
                                     'text': text_edit
                                 }, follow=True
                         )
        urls = [reverse('index'),
                reverse('profile', kwargs={'username': self.test_user.username}),
                reverse('post', kwargs={'username': self.test_user.username, 'post_id': post.id}),
                reverse(
                    'group_posts',
                    kwargs={
                        "slug": group2.slug
                    }
                ), ]
        for url in urls:
            self.check_post_variable(url, text=text_edit, group=group2, author=self.test_user)
        response = self.client.get(reverse('group_posts', kwargs={"slug": self.testgroup.slug}))
        self.assertEqual(len(response.context["posts"]), 0)
        paginator = response.context.get('paginator')
        count = paginator.count
        self.assertEqual(count, 0)


class Page_not_found_404(TestCase):

    def setUp(self):
        self.client = Client()

    def test_page_not_found_404(self):
        url="not_page"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class TestCache(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_user = User.objects.create(username='TestUser', password='testPass')
        self.client.force_login(self.test_user)
        self.post = Post.objects.create(
            author=self.test_user,
            text='text',
            )

    def test_cache(self):
        self.client.post(reverse('post_edit',
                                            kwargs={'username': self.test_user.username,
                                                    'post_id': self.post.id}),
                                            data = {'text': "text_edit"}, follow=True)
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'text')


class Image_test(TestCase):

    def setUp(self):
        self.client = Client()
        self.test_user = User.objects.create(username='TestUser', password='testPass')
        self.test_group = Group.objects.create(slug="test74posts", title="Test Group1", description="Test Descr.")
        self.client.force_login(self.test_user)
        self.test_image = "media/posts/320x320translate.png"
        self.not_image = "posts/admin.py"
        self.error_text = f'Загрузите изображение. Ранее загруженный фаял не явяяется изображением'

    def check_post_variable(self, url):
        response = self.client.post(url, follow=True)
        self.assertContains(response, '<img')

    def test_image_tru(self):
        self.post = Post.objects.create(author=self.test_user,
                                   text="post with image",
                                   image=self.test_image)
        response = self.client.post(reverse('post',
                                 kwargs={'username': self.test_user.username,
                                         'post_id': self.post.id}
                                 ), follow=True
                                        )
        self.assertContains(response, '<img')

    def test_image_tru_all_page(self):
        self.post = Post.objects.create(author=self.test_user,
                                   group=self.test_group,
                                        text="post with image",
                                        image=self.test_image)
        urls = [reverse('index'),
                reverse('post',
                        kwargs={'username': self.test_user.username,
                                'post_id': self.post.id}
        ),
                reverse(
                    'group_posts',
                    kwargs={
                        "slug": self.test_group.slug
                    }
                ), ]
        for url in urls:
            self.check_post_variable(url)

    def test_image_false(self):
        self.post = Post.objects.create(author=self.test_user,
                                        text="post with image",
                                        image=self.test_image)
        with open(self.not_image, 'rb') as notimg:
            response = self.client.post(reverse('post_edit',
                                 kwargs={'username': self.test_user.username,
                                         'post_id': self.post.id}
                                 ),
                                        data={
                                            'author': self.test_user, 'text': 'post with image', 'image': notimg
                                        }, follow=True
                                        )
            self.assertContains(response, 'Upload a valid image. The file you uploaded was either not an image or a corrupted image.')


class TestFollowerSystem(TestCase):

    def setUp(self):
        self.client = Client()
        self.test_user = User.objects.create(username='TestUser', password='testPass')
        self.user_to_follow = User.objects.create_user(username='test_user_to_follow', password=12345)
        self.user_not_auth = User.objects.create(username='TestUsernot', password='testPassnot')
        self.client.force_login(self.test_user)
        self.text = 'test_text'
        self.post = Post.objects.create(
            text=self.text, author=self.user_to_follow)

    def test_auth_user_subscribe_unsubscribe(self):
        self.client.post(reverse('profile_follow',
                                           kwargs={'username': self.user_to_follow.username}
                                           ), follow=True)
        subscribe = Follow.objects.filter(user=self.test_user, author=self.user_to_follow)
        self.assertEqual(subscribe.count(), 1)
        self.client.post(reverse('profile_unfollow',
                                 kwargs={'username': self.user_to_follow.username}
                                 ), follow=True)
        subscribe = Follow.objects.filter(user=self.test_user, author=self.user_to_follow)
        self.assertEqual(subscribe.count(), 0)


    def test_new_post_in_subscribe(self):
        pass

    def test_not_new_post_in_not_subscribe(self):
        pass


    def test_auth_user_comment_post(self):
        self.post = Post.objects.create(author=self.test_user,
                                        text="post with image",
                                        )
        comment = self.client.post(reverse('add_comment',
                                 kwargs={'username': self.test_user.username,
                                         'post_id': self.post.id}
                                 ),
                                        data={
                                            'text': 'post with comment'
                                        }, follow=True
                                        )
        self.assertContains(comment, "post with comment")
        comments = Comment.objects.filter(author=self.test_user, post_id=self.user_to_follow.id)
        self.assertEqual(comments.count(), 1)
        response = self.client.get(reverse('post', kwargs={"username": self.user_to_follow,
                                                           "post_id": '1'}))
        self.assertNotContains(response, "post with comment")







