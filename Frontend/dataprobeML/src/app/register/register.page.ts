import { Component, OnInit } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { Router } from '@angular/router';
import { Title } from '@angular/platform-browser';
import { AlertController } from '@ionic/angular';

@Component({
  selector: 'app-register',
  templateUrl: './register.page.html',
  styleUrls: ['./register.page.scss'],
})
export class RegisterPage implements OnInit {
  username = ''
  password = ''
  errorMessage: string = ''
  email = ''
  successMessage: string='';

  constructor(
    private authService: AuthService,
    private router: Router,
    private titleService: Title,
    private alertController: AlertController,
  ) { }

  ngOnInit() {
    this.titleService.setTitle("Register");
    const spans = document.querySelectorAll('.glowing span');
    spans.forEach(span => {
      (span as HTMLElement).style.setProperty('--x', Math.random().toString());
      (span as HTMLElement).style.setProperty('--y', Math.random().toString());
      (span as HTMLElement).style.setProperty('--delay', Math.random().toString());
      (span as HTMLElement).style.setProperty('--speed', Math.random().toString());
    });
  }

  async register() {
    try {
        const response = await this.authService.register(this.username, this.password, this.email).toPromise();
        if (response && 'message' in response) {
            this.successMessage = response.message;
            this.registrationConfirm();
        } else if (response && 'error' in response) {
            this.errorMessage = response.error;
            console.log(this.errorMessage)
        }
    } catch (error) {
        this.errorMessage = 'Error during registration. Retry.';
    }
  }

  async registrationConfirm(){
    const alert = await this.alertController.create({
      header: "Account created!",
      message: "Log into your account",
      buttons:[{
        text: 'OK',
        cssClass: 'alert-button-blue',
        handler: () => {
          this.navigateToLogin()
        }
      }]
    });
    await alert.present();
  }

  navigateToLogin(){
    this.router.navigate(['/login']);
  }
}
