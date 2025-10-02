import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-callback',
  templateUrl: './callback.component.html'
})
export class CallbackComponent implements OnInit {
  user: any = null;
 loading = true;


  constructor(private route: ActivatedRoute) {}

  ngOnInit(): void {
    const resolvedData = this.route.snapshot.data['auth'];

    if (resolvedData) {
      this.user = resolvedData;
    }

    this.loading = false;
  }
}
