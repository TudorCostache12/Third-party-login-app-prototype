import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-callback',
  templateUrl: './callback.component.html'
})
export class CallbackComponent implements OnInit {
  user: any = null;
  errorMessage: string | null = null;

  constructor(private https: HttpClient) {}

  ngOnInit() {
    this.https.get('http://localhost:8000/me', { withCredentials: true })
      .subscribe({
        next: (res) => {
          this.user = res;
          this.errorMessage = null;
        },
        error: (err) => {
          console.error('Not authenticated', err);
          this.errorMessage = 'Nu ești autentificat sau tokenul este invalid.';
        }
      });
  }
}
