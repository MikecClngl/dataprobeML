from rest_framework.authtoken.models import Token
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import JSONParser
import json
import os

from .services import *
from .models import Review
from .serializer import ReviewSerializer

# Create your views here.
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')

        # Verify if a user already exist
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)

        user = User.objects.create_user(username=username, password=password, email=email)
        
        user.save()
        return JsonResponse({'message': 'User registered successfully'})

    return JsonResponse({'error': 'Invalid request'}, status=400)

# Login function
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            token, created = Token.objects.get_or_create(user=user)
            
            return JsonResponse({
                'message': 'Login successful', 
                'token': token.key,
                'username': username
            })
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@api_view(['GET', 'POST', 'DELETE', 'PUT'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def reviewApi(request, *args, **kwargs):
    pk=kwargs.get('pk')
    if request.method == 'GET':
        reviews = Review.objects.filter(user=request.user)
        reviews_data = []
        for review in reviews:
            review_data = ReviewSerializer(review).data
            review_data['file'] = request.build_absolute_uri(review.review.url)
            reviews_data.append(review_data)
        return JsonResponse(reviews_data, safe=False)
    elif request.method == 'POST':
        data = request.data

        if 'review' not in data:
            return JsonResponse({"error": "No file part in the request"}, status=400, safe=False)

        file = data['review']
        name = data.get('name')
        description = data.get('description')
        date = data.get('date')
        reviewModes = data.get('reviewModes')
        candidateColumn = data.get('candidateColumn')
        referenceColumn = data.get('referenceColumn')

        review_data = {
            'review': file,
            'name': name,
            'description': description,
            'date': date,
            'reviewModes': json.loads(reviewModes) if reviewModes else [],
            'candidateColumn': candidateColumn,
            'referenceColumn': referenceColumn,
        }

        review_serializer = ReviewSerializer(data=review_data)
        errors = []
        
        if review_serializer.is_valid():
            review_instance = review_serializer.save(user = request.user)

            file_path = review_instance.review.path

            if 'BLEU' in review_data['reviewModes']:
                try:
                    bleuScores = calculate_bleu_csv(file_path, candidateColumn, referenceColumn)
                    review_instance.bleuScore = bleuScores
                except Exception as e:
                    errors.append({"type": "BLEU", "error": str(e)})

            if 'CRYSTALBLEU' in review_data['reviewModes']:
                try:
                    result = calculate_crystal_bleu_from_csv(file_path, candidateColumn, referenceColumn)
                    crystalBleuScores = result['score']
                    review_instance.crystalBleuScore = crystalBleuScores
                    if result.get('errors'):
                        errors.extend([{"type": "CRYSTALBLEU", "error": error["error"], "row": error["row"]} for error in result['errors']])
                except Exception as e:
                    errors.append({"type": "CRYSTALBLEU", "error": str(e)})
            
            if 'CODEBLEU' in review_data['reviewModes']:
                try:
                    result = calculate_code_bleu_from_csv(file_path, candidateColumn, referenceColumn)
                    codeBleuScores = result['score']
                    review_instance.codeBleuScore = codeBleuScores
                    if result.get('errors'):
                        errors.extend([{"type": "CODEBLEU", "error": error["error"], "row": error["row"]} for error in result['errors']])
                except Exception as e:
                    errors.append({"type": "CODEBLEU", "error": str(e)})
            
            if 'METEOR' in review_data['reviewModes']:
                try:
                    result = calculate_meteor_from_csv(file_path, candidateColumn, referenceColumn)
                    meteorScore = result['score']
                    review_instance.meteorScore = meteorScore
                    if result.get('errors'):
                        errors.extend([{"type": "METEOR", "error": error["error"], "row": error["row"]} for error in result['errors']])
                except Exception as e:
                    errors.append({"type": "METEOR", "error": str(e)})

            if 'ROUGE' in review_data['reviewModes']:
                try:
                    result = calculate_rouge_from_csv(file_path, candidateColumn, referenceColumn)
                    rougeScore = result['score']
                    review_instance.rougeScore = rougeScore
                    if result.get('errors'):
                        errors.extend([{"type": "ROUGE", "error": error["error"], "row": error["row"]} for error in result['errors']])
                except Exception as e:
                    errors.append({"type": "ROUGE", "error": str(e)})
            
            review_instance.save()

            file_url = request.build_absolute_uri(review_instance.review.url)
            return JsonResponse({"message": "File uploaded successfully!", 
                                 "file_url": file_url,
                                 "name": review_instance.name,
                                 "date": review_instance.date,
                                 "bleuScore": review_instance.bleuScore,
                                 "crystalBleuScore": review_instance.crystalBleuScore,
                                 "codeBleuScore": review_instance.codeBleuScore,
                                 "rougeScore": review_instance.rougeScore,
                                 "meteorScore": review_instance.meteorScore,
                                 "candidateColumn": review_instance.candidateColumn,
                                 "referenceColumn": review_instance.referenceColumn,
                                 "errors": errors
                                 }, safe=False)  
        else:
            return JsonResponse(review_serializer.errors, status=400, safe=False)
    elif request.method == 'DELETE':
        if pk is None:
            return JsonResponse({"error": "Review ID is required"}, status=400)
        
        try:
            review = Review.objects.get(id=pk)
            review.delete()
            return JsonResponse({"message": "Review deleted successfully"}, status=204)
        except Review.DoesNotExist:
            return JsonResponse({"error": "Review not found"}, status=404)
    elif request.method == 'PUT':
        try:
            review = Review.objects.get(id=pk)
        except Review.DoesNotExist:
            return JsonResponse({'error': 'Review not found'}, status=404)

        data = JSONParser().parse(request)
        review.name = data.get('name', review.name)
        review.save()

        return JsonResponse({'message': 'Review name updated successfully'}, status=200)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

