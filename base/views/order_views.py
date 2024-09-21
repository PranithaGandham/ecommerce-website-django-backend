# Django Import
from django.core.exceptions import RequestDataTooBig
from django.shortcuts import render
from datetime import datetime

from rest_framework import status

# Rest Framework Import
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.serializers import Serializer


# Local Import
from base.products import products
from base.models import *
from base.serializers import ProductSerializer, OrderSerializer

#PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.core.files.base import ContentFile
import io

#E-Mail:
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

# views start from here

def generate_invoice_pdf(order):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Invoice title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, "Invoice")

    # Order ID
    p.setFont("Helvetica", 12)
    p.drawString(100, height - 80, f"Order ID: {order._id}")
    
    # User details
    p.drawString(100, height - 100, f"User: {order.user.username}")
    p.drawString(100, height - 120, f"Email: {order.user.email}")
    p.drawString(100, height - 140, f"Shipping Address: {order.shippingaddress.address}, {order.shippingaddress.city}, {order.shippingaddress.postalCode}, {order.shippingaddress.country}")

    # Order total
    p.drawString(100, height - 180, f"Total Price: ${order.totalPrice:.2f}")
    p.drawString(100, height - 200, f"Payment Method: {order.paymentMethod}")

    # Line break
    p.drawString(100, height - 230, "Order Items:")

    # Draw items in the order
    y = height - 250
    for item in order.orderitem_set.all():
        p.drawString(100, y, f"{item.name} - Qty: {item.qty} - Price: ${item.price:.2f}")
        y -= 20

    # Finalize PDF
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addOrderItems(request):
    user = request.user
    data = request.data
    print(data)
    orderItems = data['orderItems']

    if orderItems and len(orderItems) == 0:
        return Response({'detail': 'No Order Items', "status": status.HTTP_400_BAD_REQUEST})
    else:
        # (1) Create Order
        order = Order.objects.create(
            user=user,
            paymentMethod=data['paymentMethod'],
            taxPrice=data['taxPrice'],
            shippingPrice=data['shippingPrice'],
            totalPrice=data['totalPrice'],
        )

        # (2) Create Shipping Address

        shipping = ShippingAddress.objects.create(
            order=order,
            address=data['shippingAddress']['address'],
            city=data['shippingAddress']['city'],
            postalCode=data['shippingAddress']['postalCode'],
            country=data['shippingAddress']['country'],
        )

        # (3) Create order items

        for i in orderItems:
            product = Product.objects.get(_id=i['product'])

            item = OrderItem.objects.create(
                product=product,
                order=order,
                name=product.name,
                qty=i['qty'],
                price=i['price'],
                image=product.image.url,
            )

            # (4) Update Stock

            product.countInStock -= item.qty
            product.save()

        serializer = OrderSerializer(order, many=False)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getMyOrders(request):
    user = request.user
    orders = user.order_set.all()
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def getOrders(request):
    orders = Order.objects.all()
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getOrderById(request, pk):

    user = request.user

    try:
        order = Order.objects.get(_id=pk)
        if user.is_staff or order.user == user:
            serializer = OrderSerializer(order, many=False)
            return Response(serializer.data)
        else:
            Response({'detail': 'Not Authorized  to view this order'},
                     status=status.HTTP_400_BAD_REQUEST)
    except:
        return Response({'detail': 'Order does not exist'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateOrderToPaid(request, pk):
    try:
        order = Order.objects.get(_id=pk)
        order.isPaid = True
        order.paidAt = datetime.now()
        order.save()

        # Generate invoice PDF
        pdf = generate_invoice_pdf(order)

        # Prepare the email
        subject = 'Your Invoice for Order has been Paid'
        message = f'Hi {order.user.username},\n\nThank you for your payment. Your order ID is {order._id} and is now marked as paid. Please find the attached invoice.\n\nBest regards,\nYour Company Name'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [order.user.email]

        # Create the email with the PDF attachment
        email = EmailMultiAlternatives(subject, message, from_email, recipient_list)
        email.attach(f'invoice_{order._id}.pdf', pdf, 'application/pdf')
        email.send()

        return Response('Order was paid and invoice sent', status=status.HTTP_200_OK)
    
    except Order.DoesNotExist:
        return Response({'detail': 'Order does not exist'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAdminUser])
def updateOrderToDelivered(request, pk):
    order = Order.objects.get(_id=pk)
    order.isDeliver = True
    order.deliveredAt = datetime.now()
    order.save()
    return Response('Order was Delivered')