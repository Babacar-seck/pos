import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { ApiService, LoyaltyMembership, LoyaltyProgram } from '../services/api.service';

@Component({
  selector: 'app-loyalty-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslateModule],
  template: `
    <div class="section" data-testid="settings-loyalty-section">
      <div class="section-header">
        <h2>{{ 'SETTINGS.LOYALTY_TITLE' | translate }}</h2>
        <p>{{ 'SETTINGS.LOYALTY_SUBTITLE' | translate }}</p>
      </div>

      @if (loading()) {
        <p class="hint">{{ 'COMMON.LOADING' | translate }}</p>
      } @else if (program()) {
        <div class="form-grid">
          <label class="check-row">
            <input type="checkbox" [(ngModel)]="enabled" (ngModelChange)="dirty.set(true)" />
            <span>{{ 'SETTINGS.LOYALTY_ENABLED' | translate }}</span>
          </label>
          <label>
            <span>{{ 'SETTINGS.LOYALTY_PROGRAM_NAME' | translate }}</span>
            <input type="text" [(ngModel)]="programName" (ngModelChange)="dirty.set(true)" />
          </label>
          <label>
            <span>{{ 'SETTINGS.LOYALTY_MODE' | translate }}</span>
            <select [(ngModel)]="mode" (ngModelChange)="dirty.set(true)">
              <option value="points">{{ 'SETTINGS.LOYALTY_MODE_POINTS' | translate }}</option>
              <option value="stamps">{{ 'SETTINGS.LOYALTY_MODE_STAMPS' | translate }}</option>
            </select>
          </label>
          <label>
            <span>{{ 'SETTINGS.LOYALTY_EARN' | translate }}</span>
            <input type="number" min="0" [(ngModel)]="earnUnits" (ngModelChange)="dirty.set(true)" />
          </label>
          <label>
            <span>{{ 'SETTINGS.LOYALTY_THRESHOLD' | translate }}</span>
            <input
              type="number"
              min="1"
              [(ngModel)]="threshold"
              (ngModelChange)="dirty.set(true)"
            />
          </label>
          <label>
            <span>{{ 'SETTINGS.LOYALTY_REWARD_CENTS' | translate }}</span>
            <input
              type="number"
              min="0"
              [(ngModel)]="rewardCents"
              (ngModelChange)="dirty.set(true)"
            />
          </label>
        </div>

        @if (joinUrl()) {
          <p class="hint join-url" data-testid="loyalty-join-url">
            {{ 'SETTINGS.LOYALTY_JOIN_URL' | translate }}:
            <code>{{ joinUrl() }}</code>
          </p>
        }

        @if (walletDetail()) {
          <p class="hint">{{ walletDetail() }}</p>
        }

        <div class="actions">
          <button
            type="button"
            class="btn btn-primary"
            [disabled]="!dirty() || saving()"
            (click)="save()"
            data-testid="loyalty-save"
          >
            {{ saving() ? ('COMMON.SAVING' | translate) : ('COMMON.SAVE' | translate) }}
          </button>
          @if (saveError()) {
            <span class="error">{{ saveError() }}</span>
          }
          @if (saveOk()) {
            <span class="ok">{{ 'COMMON.SUCCESS' | translate }}</span>
          }
        </div>

        <h3>{{ 'SETTINGS.LOYALTY_MEMBERS' | translate }}</h3>
        @if (members().length === 0) {
          <p class="hint">{{ 'SETTINGS.LOYALTY_MEMBERS_EMPTY' | translate }}</p>
        } @else {
          <table class="data-table">
            <thead>
              <tr>
                <th>{{ 'COMMON.NAME' | translate }}</th>
                <th>{{ 'COMMON.EMAIL' | translate }}</th>
                <th>{{ 'SETTINGS.LOYALTY_BALANCE' | translate }}</th>
              </tr>
            </thead>
            <tbody>
              @for (m of members(); track m.id) {
                <tr>
                  <td>{{ m.display_name }}</td>
                  <td>{{ m.email || m.phone || '—' }}</td>
                  <td>{{ m.balance }}</td>
                </tr>
              }
            </tbody>
          </table>
        }
      }
    </div>
  `,
  styles: [
    `
      .section-header h2 {
        margin: 0 0 0.25rem;
      }
      .section-header p,
      .hint {
        color: var(--text-muted, #666);
        margin: 0 0 1rem;
      }
      .form-grid {
        display: grid;
        gap: 0.75rem;
        max-width: 28rem;
        margin-bottom: 1rem;
      }
      .form-grid label {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
      }
      .check-row {
        flex-direction: row !important;
        align-items: center;
        gap: 0.5rem !important;
      }
      .actions {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
      }
      .error {
        color: #b00020;
      }
      .ok {
        color: #0a7a2f;
      }
      .join-url code {
        word-break: break-all;
      }
      .data-table {
        width: 100%;
        border-collapse: collapse;
      }
      .data-table th,
      .data-table td {
        text-align: left;
        padding: 0.4rem 0.5rem;
        border-bottom: 1px solid #ddd;
      }
    `,
  ],
})
export class LoyaltySettingsComponent implements OnInit {
  private api = inject(ApiService);

  loading = signal(true);
  saving = signal(false);
  dirty = signal(false);
  saveError = signal('');
  saveOk = signal(false);
  program = signal<LoyaltyProgram | null>(null);
  members = signal<LoyaltyMembership[]>([]);
  joinUrl = signal('');
  walletDetail = signal('');

  enabled = false;
  programName = 'Club';
  mode: 'points' | 'stamps' = 'points';
  earnUnits = 1;
  threshold = 10;
  rewardCents = 500;

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.loading.set(true);
    this.api.getLoyaltyProgram().subscribe({
      next: (p) => {
        this.program.set(p);
        this.enabled = !!p.enabled;
        this.programName = p.program_name || 'Club';
        this.mode = p.mode === 'stamps' ? 'stamps' : 'points';
        this.earnUnits = p.earn_units_per_order;
        this.threshold = p.redemption_threshold;
        this.rewardCents = p.reward_discount_cents;
        this.joinUrl.set(
          typeof window !== 'undefined' && p.join_path
            ? `${window.location.origin}${p.join_path}`
            : p.join_path || '',
        );
        this.walletDetail.set(p.wallet?.detail || '');
        this.dirty.set(false);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.saveError.set('Failed to load loyalty program');
      },
    });
    this.api.listLoyaltyMemberships().subscribe({
      next: (rows) => this.members.set(rows || []),
      error: () => this.members.set([]),
    });
  }

  save(): void {
    this.saving.set(true);
    this.saveError.set('');
    this.saveOk.set(false);
    this.api
      .updateLoyaltyProgram({
        enabled: this.enabled,
        program_name: this.programName,
        mode: this.mode,
        earn_units_per_order: Number(this.earnUnits) || 0,
        redemption_threshold: Math.max(1, Number(this.threshold) || 1),
        reward_discount_cents: Math.max(0, Number(this.rewardCents) || 0),
      })
      .subscribe({
        next: () => {
          this.saving.set(false);
          this.saveOk.set(true);
          this.reload();
        },
        error: (err) => {
          this.saving.set(false);
          this.saveError.set(err?.error?.detail || 'Save failed');
        },
      });
  }
}
