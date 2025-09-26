import { Routes } from '@angular/router';
import { LoginComponent } from './login/login.component';
import { CallbackComponent } from './callback/callback.component';
import { AuthResolver } from './auth-resolver.service';

export const routes: Routes = [ 
    { path: '', redirectTo: '/login', pathMatch: 'full' }, 
    { path: 'login', component: LoginComponent }, 
    { path: 'callback', component: CallbackComponent, resolve: { auth: AuthResolver }}, ];