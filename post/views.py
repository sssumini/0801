from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import Post, Comment
from .serializers import PostSerializer, CommentSerializer, PostListSerializer
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .permissions import IsOwnerOrReadOnly
# Create your views here.

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer
    
    @action(methods=["GET"], detail=False)
    def recommend(self, request):
        ran_post = self.get_queryset().order_by("-likes")[:3]
        ran_post_serializer = PostListSerializer(ran_post, many=True)
        return Response(ran_post_serializer.data)

    
    @action(methods=["GET"], detail=True)
    def test(self, request, pk=None):
        test_post = self.get_object()
        test_post.likes += 1
        test_post.save(update_fields=["likes"])
        return Response()

    def get_permissions(self):
        if self.action in ["update", "destroy", "partial_update"]:
            return [IsOwnerOrReadOnly()]
        return []
    
    def get_object(self):
        obj = super().get_object()
        return obj

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        return PostSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        post = serializer.instance
        self.handle_tags(post)
        return Response(serializer.data)
    
    def perform_update(self, serializer):
        post = serializer.save()
        #post.tag.clear()
        #self.handle_tags(post)

    def handle_tags(self, post):
        words = post.content.split(' ')
        tag_list = []
        for w in words:
            if w[0] == '#':
                tag_list.append(w[1:])
        
        for t in tag_list:
            tag, created = Tag.objects.get_or_create(name=t)
            post.tag.add(tag)
        
        post.save()

    
class CommentViewSet(
    viewsets.GenericViewSet, 
    mixins.RetrieveModelMixin, 
    mixins.UpdateModelMixin, 
    mixins.DestroyModelMixin,
):
    
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    
    def get_permissions(self):
        if self.action in ["update", "destroy", "partial_update"]:
            return [IsOwnerOrReadOnly()]
        return []
    
    def get_object(self):
        obj = super().get_object()
        return obj

class PostCommentViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin
):
    #queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        post = self.kwargs.get("post_id")
        queryset = Comment.objects.filter(post_id=post)
        return queryset

    #def list(self, request, post_id=None):
    #    post = get_object_or_404(Post, id=post_id)
    #    queryset = self.filter_queryset(self.get_queryset().filter(post=post))
    #    serializer = self.get_serializer(queryset, many=True)
    #    return Response(serializer.data)
    
    def create(self,request, post_id=None):
        post = get_object_or_404(Post, id=post_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(post=post)
        return Response(serializer.data)