from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Order, OrderItem
from cart.utils.cart import Cart


# @login_required
# def create_order(request):
#     cart = Cart(request)
#     order = Order.objects.create(user=request.user)
#     for item in cart:
#         OrderItem.objects.create(
#             order=order, product=item['product'],
#             price=item['price'], quantity=item['quantity']
#     )
#     return redirect('orders:pay_order', order_id=order.id)




import boto3



def sns_email_notification(subject, message,product, email):
    SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:298371018623:sns-cpp-x23300841"
    
    full_message = f"""Enquiry details:\n
        Product: {product}\n
        Email: {email}\n
        Message: {message}\n
    """

    try:
        # Use the correct region (eu-west-2)
        sns_client = boto3.client("sns", region_name="us-east-1",)  
        
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=full_message,
            Subject=subject
        )
        
        print(f"Email sent successfully! Message ID: {response['MessageId']}")
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False




# import requests
# import json

# @login_required
# def create_order(request):
#     cart = Cart(request)

#     # Create order
#     order = Order.objects.create(user=request.user)

#     # Create order items
#     for item in cart:
#         OrderItem.objects.create(
#             order=order,
#             product=item['product'],
#             price=item['price'],
#             quantity=item['quantity']
#         )

#     # Prepare message
#     subject = f"New Order Created - Order #{order.id}"
#     product_list = ", ".join([str(i['product']) for i in cart])
#     message = f"User {request.user} placed an order."
#     email = request.user.email if request.user.email else "No Email"

#     email_sent = sns_email_notification(
#         subject=subject,
#         message=message,
#         product=product_list,
#         email=email,
#     )

#     if email_sent:
#         print("Order created and notification email sent!")

#         # ---- CALL API GATEWAY ENDPOINT HERE ----
#         api_url = "https://fq63o2yq0i.execute-api.us-east-1.amazonaws.com/deploy/my-lambda-cpp-x23300841"
        
#         payload = {
#             "order_id": order.id,
#             "user": str(request.user),
#             "email": email,
#             "products": product_list,
#             "message": message
#         }

#         try:
#             response = requests.post(api_url, data=json.dumps(payload))
#             print("API Gateway Response:", response.text)
#         except Exception as e:
#             print("Error calling API Gateway:", str(e))

#     else:
#         print("Order created but failed to send SNS email!")

#     return redirect('orders:pay_order', order_id=order.id)


import requests
import json
from django.contrib.auth.decorators import login_required

# @login_required
# def create_order(request):
#     cart = Cart(request)

#     # Create the order
#     order = Order.objects.create(user=request.user)

#     # Create order items
#     for item in cart:
#         OrderItem.objects.create(
#             order=order,
#             product=item['product'],
#             price=item['price'],
#             quantity=item['quantity']
#         )

#     # Prepare message
#     subject = f"New Order Created - Order #{order.id}"
#     product_list = ", ".join([str(i['product']) for i in cart])
#     message = f"User {request.user} placed an order."
#     email = request.user.email if request.user.email else "No Email"

#     # Send SNS Email Notification
#     email_sent = sns_email_notification(
#         subject=subject,
#         message=message,
#         product=product_list,
#         email=email,
#     )

#     if email_sent:
#         print("Order created and notification email sent!")

#         # ---------- API Gateway Trigger ----------
#         api_url = "https://fq63o2yq0i.execute-api.us-east-1.amazonaws.com/deploy/my-lambda-cpp-x23300841"

#         # The payload we want to send to Lambda
#         payload = {
#             "order_id": order.id,
#             "name": str(request.user),
#             "email": email,
#             "products": [
#                 {
#                     "name": i['product'].title,
#                     "qty": i['quantity'],
#                     "price": float(i['price'])
#                 }
#                 for i in cart
#             ],
#             "total": sum(float(i['price']) * i['quantity'] for i in cart)
#         }

#         try:
#             # IMPORTANT: API Gateway expects { "body": "<stringified JSON>" }
#             response = requests.post(
#                 api_url,
#                 json={
#                     "body": json.dumps(payload)
#                 }
#             )

#             print("API Gateway Response:", response.text)

#         except Exception as e:
#             print("Error calling API Gateway:", str(e))

#     else:
#         print("Order created but failed to send SNS email!")

#     # Redirect to payment page
#     return redirect('orders:pay_order', order_id=order.id)




import requests
import json
from django.contrib.auth.decorators import login_required

@login_required
def create_order(request):
    cart = Cart(request)
    
    # Create order
    order = Order.objects.create(user=request.user)
    
    # Create order items
    for item in cart:
        OrderItem.objects.create(
            order=order,
            product=item['product'],
            price=item['price'],
            quantity=item['quantity']
        )
    
    # SNS email
    subject = f"New Order Created - Order #{order.id}"
    product_list = ", ".join([str(i['product']) for i in cart])
    message = f"User {request.user} placed an order."
    email = request.user.email if request.user.email else "No Email"
    
    email_sent = sns_email_notification(
        subject=subject,
        message=message,
        product=product_list,
        email=email,
    )
    
    if email_sent:
        print("Order created and notification email sent!")
    
        # Safely get user name
        user_name = (
            getattr(request.user, "full_name", None)
            or f"{request.user.first_name} {request.user.last_name}".strip()
            or request.user.username
        )
    
        # ---- Build data for Lambda ----
        products_data = [
            {
                "id": item['product'].id,
                "name": item['product'].title,
                "price": float(item['price']),
                "qty": item['quantity']
            }
            for item in cart
        ]
    
        total_amount = sum(
            item['quantity'] * float(item['price']) for item in cart
        )
    
        payload = {
            "order_id": order.id,
            "name": user_name,
            "email": email,
            "products": products_data,
            "total": total_amount
        }
    
        api_url = "https://fq63o2yq0i.execute-api.us-east-1.amazonaws.com/deploy/my-lambda-cpp-x23300841"
    
        try:
            response = requests.post(
                api_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )
            print("API Gateway Response:", response.text)
        except Exception as e:
            print("Error calling API Gateway:", str(e))
    
    else:
        print("Order created but failed to send SNS email!")
    
    return redirect('orders:pay_order', order_id=order.id)






@login_required
def checkout(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    context = {'title':'Checkout' ,'order':order}
    return render(request, 'checkout.html', context)




@login_required
def fake_payment(request, order_id):
    cart = Cart(request)
    cart.clear()
    order = get_object_or_404(Order, id=order_id)
    order.status = True
    order.save()
    return redirect('orders:user_orders')


@login_required
def user_orders(request):
    orders = request.user.orders.all()
    context = {'title':'Orders', 'orders': orders}
    return render(request, 'user_orders.html', context)