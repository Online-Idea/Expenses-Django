

# GET по модели
# class ClientAPIView(generics.ListAPIView):
#     queryset = Client.objects.all()
#     serializer_class = ClientSerializer

# GET и POST низкого уровня
# class ClientAPIView(APIView):
#     def get(self, request):
#         c = Client.objects.all()
#         return Response({'clients': ClientSerializer(c, many=True).data})
#
#     def post(self, request):
#         serializer = ClientSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#
#         return Response({'client': serializer.data})
