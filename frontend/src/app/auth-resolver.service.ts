import { Injectable } from '@angular/core';
import { Resolve, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { EMPTY, Observable, catchError } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthResolver implements Resolve<any> {
  constructor(private http: HttpClient, private router: Router) {}

  resolve(): Observable<any> {
    return this.http.get('https://localhost:8000/me', { withCredentials: true }).pipe(
      catchError(err => {
        // dacă nu există sesiune → redirect la login
        //this.router.navigate(['/login']);
        window.location.href = 'https://localhost:8000/login';
        return EMPTY;  // componenta callback nu se încarcă
      })
    );
  }
}
