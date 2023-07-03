from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.views import View
from login.models import*
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from .utils import account_activation_token
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
from django.template.loader import render_to_string
import random
import time

# ================================== User Registration Page ==================================
class User_Registraion(View):
    def get(self, request):
        return render(request, "registration.html")

    def post(self, request):
        if request.method == "POST":
            first_name = request.POST.get("firstname")
            last_name = request.POST.get("lastname")
            email = request.POST.get("email")
            username = request.POST.get("username")
            password = request.POST.get("password")
            confirm_password = request.POST.get("cpassword")
            agree = request.POST.get("agree")
            profile_pic = request.FILES.get("pic")

            value = {
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "email": email,
            }

            error_message = None
            user = UserProfile(
                first_name=first_name,
                last_name=last_name,
                email=email,
                profile_pic=profile_pic,
                username=username,
                password=password,
            )
            if not first_name:
                error_message = "First Name is Required !!"
            elif not last_name:
                error_message = "Last Name is Required !!"
            elif not username:
                error_message = "Username is Required !!"
            elif not email:
                error_message = "Email is Required !!"
            elif not password:
                error_message = "Password is Required !!"
            elif not confirm_password:
                error_message = "Confirm Password is Required !!"
            elif not password == confirm_password:
                error_message = "Password & Confirm Password Should be Same !!"
            elif user.isExists():
                error_message = "Username Already Exists !!"
            elif not agree:
                error_message = "Please Select Our Terms & Condition !!"
            if not error_message:
                
                uidb64 = urlsafe_base64_encode(force_bytes(user.username))
                domain = get_current_site(request).domain
                link = reverse("activate", kwargs={"uidb64": uidb64, "token": account_activation_token.make_token(user)})
                email_subject = "Activate Your Account" 
                activate_url = "http://"+domain+link
                email_from = settings.EMAIL_HOST_USER 
                recipient_list = [email]
                mydict = {"username":username, "activate_url": activate_url}
                html_template = 'account_activation.html'
                html_message = render_to_string(html_template, context=mydict )

                email = EmailMessage(email_subject,html_message,email_from,recipient_list)
                email.content_subtype="html"
                email.send()
                user.save()
                messages.success(request,"Account Created Successfully! Please Check Mail to Activate your Account!")
                return redirect("user_login")
            else:
                data = {
                    "error": error_message,
                    "value": value,
                }
                return render(request, "registration.html", data)


# ===========================================================================================




# =================================== Login Page =============================================
class User_Login(View):
    def get(self, request):
        return render(request, "login.html")

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")

        value = {
            'username' : username,
        }

        error_message = None
        user = UserProfile.get_user_by_username(username)
        if user:
            if password == user.password:
                if user.status == False:
                    error_message = "Account is not activated"
                else:
                    return HttpResponse("Homepage")
            else:
                error_message = "Invalid password"
        else:
            error_message = "invalid username"

        return render(request, "login.html",{'error': error_message, 'value': value})
# ===========================================================================================

class VerificationView(View):
    def get(self,request,uidb64,token):
        try:
            username = force_str(urlsafe_base64_decode(uidb64))
            user = UserProfile.objects.get(username=username)
            if user.status == True:
                messages.warning(request, "Account already activated")
                return redirect("user_login")
            else:
                user.status = True
                user.save()
                messages.success(request, "Account activated successfully")
        except Exception as ex:
            pass
        return redirect("user_login")

#////////////////// FORGOT PASSWORD ///////////////////# 

def forgot_password(request):
    return render(request, 'forgot_password.html')

#////////////////// SEND OTP ///////////////////#

def send_otp(request):
    error_message = None
    otp = random.randint(11111,99999)
    otp=int(time.strftime("%H%S%M")) + int(time.strftime("%S"))
    email = request.POST.get('email')
    #filter user from userprofile
    user_email = UserProfile.objects.filter(email=email)
    if user_email:
        user = UserProfile.objects.get(email=email)
        #generate and save otp
        user.otp = otp  
        user.save()
        #email saved in key----to get email in enter otp()
        request.session['email'] = request.POST['email']
        html_message = "Your one-time Password : - " + "" + str(otp)
        subject = "Welcome To MLLOOPS"
        email_from = settings.EMAIL_HOST_USER
        email_to = [email]
        message = EmailMessage(subject,html_message,email_from,email_to)
        message.send()
        messages.success(request, 'One Time Password Sent To Your Email')
        return redirect('enter_otp')
    else:
        error_message = "Enter Valid Email-ID"
        return render(request, 'forgot_password.html',{'error':error_message})


#////////////////// ENTER OTP ///////////////////#

def enter_otp(request):
    error_message = None
    #get email from session key
    if request.session.has_key('email'):
        email = request.session['email']
        user = UserProfile.objects.filter(email=email)
        for u in user:
            user_otp = u.otp
        if request.method == "POST":
            otp = request.POST.get('otp')
            if not otp:
                error_message = "OTP is Required"
            #if entered otp not equal to sent otp
            elif not user_otp == otp:
                error_message = "OTP is Invalid"
            if not error_message:
                return redirect("password_reset")
        return render(request, "enter_otp.html", {'error': error_message})
    else:
        return render(request, "forgot_password.html")

#////////////////// CHANGE PASSWORD ///////////////////#

def password_reset(request):
    error_message = None
    if request.session.has_key('email'):
        email = request.session['email']
        user = UserProfile.objects.get(email=email)
        if request.method == "POST":
            new_password = request.POST.get('new_password')
            confirm_new_password = request.POST.get('confirm_new_password')
            if not new_password:
                error_message = "Enter new password!"
            elif not confirm_new_password:
                error_message = "Enter New Confirm Password!"
            if not error_message:
                user.password = new_password
                user.save() 
                messages.success(request,"Password Changed Successfully")
                #password chnaged email
                html_message = "Your Password Changed Successfully"
                subject = "Welcome To Python World"
                email_from = settings.EMAIL_HOST_USER
                email_to = [email]
                message = EmailMessage(subject,html_message,email_from,email_to)
                message.send()
                
                return redirect("user_login")
    return render(request, "password_reset.html", {'error':error_message})

