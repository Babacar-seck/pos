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
        @if (vipTier()) {
          <p class="tier" data-testid="loyalty-card-vip">
            {{ 'LOYALTY_PUBLIC.VIP_TIER' | translate }}: <strong>{{ vipTier() }}</strong>
          </p>
        }
        @if (referralCode() && tenantId()) {
          <p class="hint">{{ 'LOYALTY_PUBLIC.REFERRAL_SHARE' | translate }}</p>
          <p class="token">
            <code>{{ origin }}/loyalty/{{ tenantId() }}?ref={{ referralCode() }}</code>
          </p>
        }
      }
    </div>
  `,
  styles: [
    `
      .loyalty-card {
        padding: 1.5rem;
      }
      .balance,
      .tier {
        font-size: 1.25rem;
      }
      .error {
        color: #b00020;
      }
      .hint {
        color: var(--text-muted, #666);
      }
      .token code {
        word-break: break-all;
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
  vipTier = signal<string | null>(null);
  referralCode = signal<string | null>(null);
  tenantId = signal<number | null>(null);
  origin =
    typeof window !== 'undefined' && window.location?.origin
      ? window.location.origin
      : '';

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
        this.vipTier.set(res.membership.vip_tier ?? null);
        this.referralCode.set(res.membership.referral_code ?? null);
        this.tenantId.set(res.membership.tenant_id ?? null);
        this.loading.set(false);
      },
      error: () => {
        this.error.set(true);
        this.loading.set(false);
      },
    });
  }
}
