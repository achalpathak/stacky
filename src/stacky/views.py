import sys
import requests
from django.shortcuts import render
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
from django.core.cache import cache
from django.core.paginator import Paginator

# Create your views here.
class AnonDayThrottle(AnonRateThrottle):
     scope = 'anon_day'
     
def home(request):
    return render(request, 'index.html')


@api_view(['POST'])
@throttle_classes([AnonRateThrottle,AnonDayThrottle])
def search_stack(request):
    try:
        if request.method == 'POST':
            input_params = {
                'q': request.data.get('q'),
                'accepted': request.data.get('accepted'),
                'answers': request.data.get('answers'),
                'body': request.data.get('body'),
                'closed': request.data.get('closed'),
                'migrated': request.data.get('migrated'),
                'notice': request.data.get('notice'),
                'not_tagged': request.data.get('not_tagged'),
                'tagged': request.data.get('tagged'),
                'title': request.data.get('title'),
                'user_id': request.data.get('user_id'),
                'url': request.data.get('url'),
                'views': request.data.get('views'),
                'wiki': request.data.get('wiki'),
                'order': request.data.get('order'),
                'sort': request.data.get('sort')
            }
            stack_url = "https://api.stackexchange.com/2.2/search/advanced?"
            empty_flag = True
            # add parameters dynamically to the url if it is not NONE
            for key, value in input_params.items():
                if value:
                    empty_flag = False
                if value is not None:
                    stack_url += '%s=%s&' % (key, value)
                    
            if empty_flag:
                # will raise error if no parameters are supplied
                raise ValueError('No input parameters supplied.')
            
            stack_url += 'site=stackoverflow'
            if cache.get(stack_url):
                # Request will be served from cache
                data = cache.get(stack_url)
            else:
                # If it is not present in the cache a request will be made to stackoverflow api
                response = requests.get(stack_url)
                data = response.json()
                # add new entry to cache
                cache.set(stack_url, data)
                
            # default value set as 10 items per page
            p = Paginator(data['items'], 10)
            if request.data.get('page_number'):
                data["items"]=p.page(request.data.get('page_number')).object_list
            else:
                data["items"]=p.page(1).object_list
            data['pages']= p.num_pages

            
            res = {'data':data}
            status_code = status.HTTP_200_OK
            return Response(res, status=status_code)
    except KeyError as e:
        
        res = {
            'error': 'Keys missing-{}'.format(e)}
        return Response(res, status=status.HTTP_400_BAD_REQUEST)
    except ValueError as e:
        print(e)
        res = {'error': str(e)}
        return Response(res, status=status.HTTP_400_BAD_REQUEST)
    except PermissionError:
        res = {'error': 'you are unauthorized to perform the following action.'}
        return Response(res, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        # will print the exception and line number for easy debugging
        print(e)
        trace_back = sys.exc_info()[2]
        line = trace_back.tb_lineno
        print(line)
        res = {'error': 'some error occured'}
        return Response(res, status=status.HTTP_400_BAD_REQUEST)
