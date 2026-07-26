import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { ApiService } from '../services/api.service';
import { LanguagePickerComponent } from '../shared/language-picker.component';

@Component({
  selector: 'app-loyalty-card-public',
  standalone: true,
  imports: [TranslateModule, LanguagePickerComponent],
  template: `
    <div class="book-page loyalty-card" data-testid="loyalty-card-page">
      <app-language-picker></app-language-picker>
      @if (loading()) {
        <p>{{ 'COMMON.LOADING' | translate }}</p>
      } @else if (error()) {
        <p class="error">{{ 'LOYALTY_PUBLIC.CARD_NOT_FOUND' | translate }}</p>
      } @else {
        <h1>{{ programName() }}</h1>
        <p>{{ displayName() }}</p>
        <p class="balance">
          {{ 'LOYALTY_PUBLIC.BALANCE' | translate }}: <strong>{{ balance() }}</strong>
        </p>
      }
    </div>
  `,
  styles: [
    `
      .loyalty-card {
        padding: 1.5rem;
      }
      .balance {
        font-size: 1.25rem;
      }
      .error {
        color: #b00020;
      }
    `,
  ],
})
export class LoyaltyCardPublicComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private api = inject(ApiService);

  loading = signal(true);
  error = signal(false);
  programName = signal('');
  displayName = signal('');
  balance = signal(0);

  ngOnInit(): void {
    const token = this.route.snapshot.paramMap.get('memberToken') || '';
    if (!token) {
      this.error.set(true);
      this.loading.set(false);
      return;
    }
    this.api.getPublicLoyaltyBalance(token).subscribe({
      next: (res) => {
        this.programName.set(res.program?.program_name || '');
        this.displayName.set(res.membership.display_name);
        this.balance.set(res.membership.balance);
        this.loading.set(false);
      },
      error: () => {
        this.error.set(true);
        this.loading.set(false);
      },
    });
  }
}
