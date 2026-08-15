import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import {
  ApiService,
  DeliveryCatalogMappingRow,
  DeliveryConnectionBadge,
  DeliveryIntegrationEventRow,
  DeliveryIntegrationPublic,
  DeliveryProviderCatalogRow,
  Product,
} from '../services/api.service';

const BADGE_TRANSLATION_KEY: Record<DeliveryConnectionBadge, string> = {
  disconnected: 'SETTINGS.DELIVERY_INTEGRATIONS_BADGE_DISCONNECTED',
  pending_test: 'SETTINGS.DELIVERY_INTEGRATIONS_BADGE_PENDING_TEST',
  connected: 'SETTINGS.DELIVERY_INTEGRATIONS_BADGE_CONNECTED',
  error: 'SETTINGS.DELIVERY_INTEGRATIONS_BADGE_ERROR',
};

const BRAND_PALETTE = ['#5B4FE9', '#00A67D', '#FF5A5F', '#0A84FF', '#F4A100', '#8E44AD'];

/**
 * Official brand marks (icon path + brand color) for providers with a real integration.
 * SVG path data sourced from the Simple Icons project (github.com/simple-icons/simple-icons,
 * CC0 icon data); each mark remains a trademark of its respective owner. Shown only in this
 * internal settings screen to identify which marketplace an integration connects to — not used
 * in customer-facing branding. Unknown provider_keys (e.g. "stub") fall back to a lettered pastille.
 */
const PROVIDER_BRAND: Record<string, { color: string; path: string }> = {
  uber_eats: {
    color: '#06C167',
    path: 'M0 2.8645v4.9972c0 1.8834 1.3315 3.1297 3.0835 3.1297a2.9652 2.9652 0 0 0 2.1502-.876v.7425H6.445V2.8645H5.223v4.9339c0 1.2642-.8696 2.1198-1.9954 2.122-1.1386-.0023-1.997-.834-1.997-2.122V2.8645zm7.3625 0v7.9934h1.163v-.7318a2.9915 2.9915 0 0 0 2.1177.876c1.714.048 3.1295-1.3283 3.1295-3.0429s-1.4155-3.091-3.1295-3.0429a2.9674 2.9674 0 0 0-2.107.876V2.8645zm9.8857 2.0561c-1.6752-.0074-3.0369 1.3492-3.0356 3.0245 0 1.7366 1.3732 3.0373 3.1537 3.0373a3.123 3.123 0 0 0 2.5578-1.2438l-.8495-.6177a2.0498 2.0498 0 0 1-1.7083.8585c-.9763.0126-1.8147-.6915-1.971-1.6553h4.818v-.379c0-1.734-1.254-3.0238-2.9638-3.0245zm6.1632.0667a1.5943 1.5943 0 0 0-1.376.7657v-.7186h-1.163v5.8235h1.1741V7.5465c0-.9023.5581-1.4847 1.3268-1.4847h.4949V4.9886c-.1576.0013-.3186-.0009-.4568-.0013zm-6.2034.944a1.844 1.844 0 0 1 1.8337 1.486H15.424a1.844 1.844 0 0 1 1.784-1.486zm-6.6589.0056c1.1223-.0084 2.0365.8992 2.0364 2.0215-.0026 1.1203-.914 2.0258-2.0343 2.021a2.0151 2.0151 0 0 1-1.4159-.5987A2.0152 2.0152 0 0 1 8.55 7.9592a2.0152 2.0152 0 0 1 .5838-1.422 2.0152 2.0152 0 0 1 1.4153-.6003zM0 12.9864v7.9716h5.7222v-1.3666H1.5458v-1.971h4.0647v-1.314H1.5458v-1.9556h4.1764v-1.3644zm14.5608.4097v1.6861h-1.1519v1.338h1.1545v3.143c0 .7927.5712 1.4209 1.6005 1.4209h1.6425L17.8 19.646h-1.1412c-.3482 0-.5714-.1509-.5714-.464v-2.7683H17.8v-1.3316h-1.7062v-1.686zm-5.2974 1.5275c-1.7348-.0103-3.141 1.4035-3.1214 3.1382.0196 1.7346 1.4575 3.1163 3.1915 3.0668a2.9915 2.9915 0 0 0 1.912-.6655v.532h1.5175v-5.9129h-1.509v.5257a3.0047 3.0047 0 0 0-1.9205-.6835c-.0244-.0007-.0492-.0006-.0701-.0008zm11.771.0077c-1.5855 0-2.7002.6437-2.7002 1.8854 0 .8607.6132 1.4213 1.936 1.695l1.4478.3286c.5694.1095.7224.2585.7224.4906 0 .3701-.438.6022-1.1279.6022-.876 0-1.3774-.1907-1.5723-.8477h-1.533c.219 1.2307 1.1563 2.05 3.0484 2.05h.0022c1.752 0 2.7422-.819 2.7422-1.9534 0-.8059-.5847-1.4084-1.8089-1.6668l-1.2943-.2605c-.7511-.1358-.988-.2738-.988-.5454 0-.357.3616-.5757 1.0295-.5757.7227 0 1.2527.1925 1.406.8473h1.5175c-.0854-1.2286-.9899-2.0497-2.8273-2.0497zM9.467 16.1815c1.0092.0096 1.8188.8369 1.8067 1.8461.0014 1.0046-.8198 1.816-1.8243 1.8025-1.0075-.0048-1.8203-.8256-1.8155-1.833.0048-1.0076.8255-1.8204 1.833-1.8156z',
  },
  glovo: {
    color: '#FFC244',
    path: 'M12.012 0C7.847 0 4.459 3.388 4.459 7.553c0 1.576.494 3.106 1.412 4.4l.211.281 3.93 5.555s.47.775 1.529.775h.941c1.036 0 1.53-.775 1.53-.775l3.93-5.555.187-.28a7.43 7.43 0 0 0 1.412-4.401C19.564 3.388 16.176 0 12.011 0Zm0 3.693a3.837 3.837 0 0 1 3.836 3.836c0 .824-.26 1.578-.73 2.237l-.212.28-2.894 4.095-2.895-4.07-.21-.305a3.848 3.848 0 0 1-.731-2.237 3.837 3.837 0 0 1 3.836-3.836zm-2.117 18.26c0 1.106.893 2.023 2.07 2.047 1.223 0 2.117-.917 2.117-2.059 0-1.14-.894-2.058-2.094-2.058-1.2 0-2.093.917-2.093 2.07z',
  },
  deliveroo: {
    color: '#00CCBC',
    path: 'M16.861 0l-1.127 10.584L13.81 1.66 7.777 2.926l1.924 8.922-8.695 1.822 1.535 7.127L17.832 24l3.498-7.744L22.994.636 16.861 0zM11.39 13.61a.755.755 0 01.322.066c.208.093.56.29.63.592.103.434.004.799-.312 1.084v.002c-.315.284-.732.258-1.174.113-.441-.145-.637-.672-.47-1.309.124-.473.71-.544 1.004-.549zm4.142.548c.447-.012.832.186 1.05.543.217.357.107.75-.122 1.143h-.002c-.229.392-.83.445-1.422.16-.399-.193-.397-.684-.353-.983a.922.922 0 01.193-.447c.142-.177.381-.408.656-.416Z',
  },
  just_eat: {
    color: '#FF8000',
    path: 'M20.6138 7.1997c-.0019-.0024-.0716-.0708-.0867-.2003a37.1998 37.1998 0 0 0-.5677-4.0793.6637.6637 0 0 0-.575-.516l-1.9612-.2364c0 .0002-.0213-.0027-.0516 0a.4129.4129 0 0 0-.4129.4128v.6792c.0071.0337-.0345.0156-.0412.0186A27.5178 27.5178 0 0 0 12.9723.2931c-.366-.245-.7355-.293-.9692-.293-.5918-.0016-.9527.293-.9693.293C4.277 4.4686.559 11.243.4155 11.6146c-.1799.3807.0325.8309.4407.9341l1.9457.3747a.6668.6668 0 0 1 .4862.5688c.0155.3437.384 8.0161.8454 10.0062.0076.0609.1743.4985.6482.4986h.0145c1.1318-.0299 2.2639-.0485 3.396-.063a.2198.2198 0 0 0 .2178-.2188c0-.1794-.0283-.0597-.2312-3.9565a.4129.4129 0 0 0-.2024-.323 2.0985 2.0985 0 0 1-1.0208-1.695c-.2262-5.8941.0116-8.2329-.0072-8.2329.0112-.528.8097-.5116.7824.0465-.11 1.8084-.0902 3.6209-.0702 5.4315.0106.6197.9396.6032.929-.0165-.0351-1.9045-.0248-3.8347.0733-5.4615.0065-.5085.7941-.529.7824.0465-.1067 1.7985-.0933 3.601-.0702 5.4016.0097.6192.9387.6048.929-.0145.011.011-.0846-2.8339.0733-5.4346.0112-.528.7824-.5194.7824.0464-.1515 2.6902-.0805 5.386 0 8.0771a2.0975 2.0975 0 0 1-.9104 1.731.4046.4046 0 0 0-.1734.3045s-.0475.4036.13 2.3576c.0542.5713.116 1.1418.1766 1.7125a.2064.2064 0 0 0 .2064.1796 468.6068 468.6068 0 0 1 4.0556.0093.2064.2064 0 0 0 .2064-.1817c.256-2.3421.3159-3.6582.3159-3.6582a.2323.2323 0 0 0-.2065-.225l-1.3419-.1848c.0058.0119-.4402-.0659-.4005-.5347.5357-7.8107 3.109-10.4398 3.109-10.4398a.8257.8257 0 0 1 .125-.1032c.2186-.1583.528-.0676.6265.1837a.8132.8132 0 0 1 .033.188c.222 2.4535.1136 6.6298-.0237 9.8875-.1167 2.7653-.258 4.936-.258 4.936 0 .089.072.161.161.161.7425.0117 1.485.0293 2.2275.0465a.671.671 0 0 0 .6482-.4986c.4614-1.99.8258-9.6625.8454-10.0062a.6647.6647 0 0 1 .4862-.5688l1.9457-.3747c.4082-.1032.6206-.5534.4407-.9341-.0355-.0956-.918-1.8515-2.9707-4.418z',
  },
};

@Component({
  selector: 'app-delivery-integrations-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslateModule],
  template: `
    <div class="section" data-testid="settings-delivery-integrations-section">
      <div class="section-header">
        <h2>{{ 'SETTINGS.DELIVERY_INTEGRATIONS_TITLE' | translate }}</h2>
        <p>{{ 'SETTINGS.DELIVERY_INTEGRATIONS_SUBTITLE' | translate }}</p>
      </div>

      @if (loading()) {
        <p class="hint">{{ 'COMMON.LOADING' | translate }}</p>
      } @else {
        @for (row of mergedRows(); track row.provider_key) {
          <div class="provider-card">
            <div class="provider-head">
              <div class="provider-identity">
                <div class="brand-pastille" [style.background]="providerColor(row.provider_key)">
                  @if (providerIconPath(row.provider_key); as iconPath) {
                    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
                      <path [attr.d]="iconPath" fill="currentColor" />
                    </svg>
                  } @else {
                    {{ providerInitial(row.display_name) }}
                  }
                </div>
                <div>
                  <h3>{{ row.display_name }}</h3>
                  <p class="hint">{{ tenantName() || row.provider_key }}</p>
                  @if (row.integration?.last_order_received_at) {
                    <p class="hint">
                      {{ 'SETTINGS.DELIVERY_INTEGRATIONS_LAST_ORDER' | translate }}:
                      {{ row.integration!.last_order_received_at }}
                    </p>
                  }
                </div>
              </div>
              <div class="provider-head-actions">
                <span class="status-badge" [ngClass]="badgeClass(row)">{{
                  badgeKey(row) | translate
                }}</span>
                @if (row.integration?.id) {
                  <label class="quick-toggle">
                    <input
                      type="checkbox"
                      [checked]="row.integration!.enabled"
                      [disabled]="saving()"
                      (change)="quickToggle(row)"
                    />
                    <span>{{ 'SETTINGS.DELIVERY_INTEGRATIONS_QUICK_TOGGLE' | translate }}</span>
                  </label>
                }
                <button
                  type="button"
                  class="btn btn-sm btn-secondary"
                  (click)="toggleExpand(row.provider_key)"
                >
                  {{
                    expanded() === row.provider_key
                      ? ('SETTINGS.DELIVERY_INTEGRATIONS_COLLAPSE' | translate)
                      : ('SETTINGS.DELIVERY_INTEGRATIONS_EXPAND' | translate)
                  }}
                </button>
              </div>
            </div>

            @if (expanded() === row.provider_key) {
              <div class="provider-body">
                <label class="chk">
                  <input type="checkbox" [(ngModel)]="draftEnabled[row.provider_key]" />
                  <span>{{ 'SETTINGS.DELIVERY_INTEGRATIONS_ENABLED' | translate }}</span>
                </label>

                <label>
                  <span>{{ 'SETTINGS.DELIVERY_INTEGRATIONS_STORE_ID' | translate }}</span>
                  <input
                    type="text"
                    [(ngModel)]="draftStoreId[row.provider_key]"
                    [placeholder]="'SETTINGS.DELIVERY_INTEGRATIONS_STORE_ID_PH' | translate"
                  />
                </label>

                <label>
                  <span>{{ 'SETTINGS.DELIVERY_INTEGRATIONS_CREDENTIALS_JSON' | translate }}</span>
                  <textarea
                    rows="5"
                    class="mono"
                    [(ngModel)]="draftCredentialsJson[row.provider_key]"
                    [placeholder]="credentialsPlaceholder()"
                  ></textarea>
                  <span class="hint">{{
                    'SETTINGS.DELIVERY_INTEGRATIONS_CREDENTIALS_HINT' | translate
                  }}</span>
                </label>

                <div class="btn-row">
                  <button
                    type="button"
                    class="btn btn-primary"
                    [disabled]="saving()"
                    (click)="save(row)"
                  >
                    {{ saving() ? ('COMMON.SAVING' | translate) : ('COMMON.SAVE' | translate) }}
                  </button>
                  @if (row.integration?.id) {
                    <button
                      type="button"
                      class="btn btn-secondary"
                      [disabled]="testing()"
                      (click)="runTest(row)"
                    >
                      {{ 'SETTINGS.DELIVERY_INTEGRATIONS_TEST' | translate }}
                    </button>
                  }
                </div>

                @if (row.integration?.id) {
                  <div class="webhook-box">
                    <strong>{{ 'SETTINGS.DELIVERY_INTEGRATIONS_WEBHOOK_URL' | translate }}</strong>
                    <div class="mono wrap">{{ row.integration!.webhook_url_hint }}</div>
                    <button
                      type="button"
                      class="btn btn-sm btn-secondary"
                      (click)="copyUrl(row.integration!)"
                    >
                      {{ 'SETTINGS.DELIVERY_INTEGRATIONS_COPY_URL' | translate }}
                    </button>
                  </div>

                  <div class="status-row">
                    <span>{{ 'SETTINGS.DELIVERY_INTEGRATIONS_LAST_TEST' | translate }}:</span>
                    @if (row.integration!.last_test_at) {
                      <span>{{ row.integration!.last_test_at }}</span>
                      @if (row.integration!.last_test_ok === true) {
                        <span class="ok">{{
                          'SETTINGS.DELIVERY_INTEGRATIONS_STATUS_OK' | translate
                        }}</span>
                      } @else if (row.integration!.last_test_ok === false) {
                        <span class="bad">{{
                          'SETTINGS.DELIVERY_INTEGRATIONS_STATUS_FAIL' | translate
                        }}</span>
                      }
                    } @else {
                      <span class="hint">—</span>
                    }
                  </div>

                  <h4>{{ 'SETTINGS.DELIVERY_INTEGRATIONS_MAPPINGS' | translate }}</h4>
                  <p class="hint">
                    {{ 'SETTINGS.DELIVERY_INTEGRATIONS_MAPPINGS_HINT' | translate }}
                  </p>
                  <div class="sync-stats">
                    <span>
                      {{ 'SETTINGS.DELIVERY_INTEGRATIONS_MAPPING_COUNT' | translate }}:
                      {{ row.integration!.mapping_count }}
                      @if (row.integration!.mapping_last_modified_at) {
                        <span class="hint">
                          ({{ 'SETTINGS.DELIVERY_INTEGRATIONS_MAPPING_MODIFIED' | translate }}
                          {{ row.integration!.mapping_last_modified_at }})
                        </span>
                      }
                    </span>
                    <span [class.bad]="row.integration!.unmapped_rejections_7d > 0">
                      {{ 'SETTINGS.DELIVERY_INTEGRATIONS_UNMAPPED_REJECTIONS' | translate }}:
                      {{ row.integration!.unmapped_rejections_7d }}
                    </span>
                  </div>
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>{{ 'SETTINGS.DELIVERY_INTEGRATIONS_EXT_SKU' | translate }}</th>
                        <th>{{ 'SETTINGS.DELIVERY_INTEGRATIONS_PRODUCT' | translate }}</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      @for (m of mappingDraft[row.provider_key]; track $index) {
                        <tr>
                          <td>
                            <input
                              type="text"
                              [(ngModel)]="m.external_item_id"
                              class="inline-input"
                            />
                          </td>
                          <td>
                            <select [(ngModel)]="m.product_id" class="inline-select">
                              <option [ngValue]="null">{{ 'COMMON.NONE' | translate }}</option>
                              @for (p of products(); track p.id) {
                                <option [ngValue]="p.id">{{ p.name }} (#{{ p.id }})</option>
                              }
                            </select>
                          </td>
                          <td class="actions">
                            <button
                              type="button"
                              class="btn btn-sm btn-secondary"
                              (click)="removeMapping(row, $index)"
                            >
                              {{ 'COMMON.DELETE' | translate }}
                            </button>
                          </td>
                        </tr>
                      }
                    </tbody>
                  </table>
                  <button type="button" class="btn btn-sm btn-secondary" (click)="addMapping(row)">
                    {{ 'SETTINGS.DELIVERY_INTEGRATIONS_ADD_MAPPING' | translate }}
                  </button>
                  <button
                    type="button"
                    class="btn btn-primary"
                    [disabled]="savingMappings()"
                    (click)="saveMappings(row)"
                  >
                    {{
                      savingMappings()
                        ? ('COMMON.SAVING' | translate)
                        : ('SETTINGS.DELIVERY_INTEGRATIONS_SAVE_MAPPINGS' | translate)
                    }}
                  </button>

                  <h4>{{ 'SETTINGS.DELIVERY_INTEGRATIONS_EVENTS' | translate }}</h4>
                  @if (eventsLoading()) {
                    <p class="hint">{{ 'COMMON.LOADING' | translate }}</p>
                  } @else if ((events[row.provider_key] || []).length === 0) {
                    <p class="hint">{{ 'SETTINGS.DELIVERY_INTEGRATIONS_NO_EVENTS' | translate }}</p>
                  } @else {
                    <ul class="event-list">
                      @for (ev of events[row.provider_key]; track ev.id) {
                        <li [class.bad]="!ev.success">
                          <span class="mono">{{ ev.created_at }}</span>
                          <strong>{{ ev.event_type }}</strong>
                          — {{ ev.summary }}
                          @if (ev.error_message) {
                            <span class="err">{{ ev.error_message }}</span>
                          }
                        </li>
                      }
                    </ul>
                  }
                }

                @if (message()) {
                  <p class="hint">{{ message() }}</p>
                }
              </div>
            }
          </div>
        }
      }
    </div>
  `,
  styles: [
    `
      .provider-card {
        border: 1px solid var(--border-subtle, #ddd);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        background: var(--panel-bg, #fff);
      }
      .provider-head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
      }
      .provider-head h3 {
        margin: 0 0 0.25rem 0;
      }
      .provider-identity {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
      }
      .provider-head-actions {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        flex-wrap: wrap;
      }
      .brand-pastille {
        flex: none;
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-weight: 700;
        font-size: 1.1rem;
      }
      .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 500;
        white-space: nowrap;
      }
      .status-badge::before {
        content: '';
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: currentColor;
      }
      .status-badge.badge-not-configured {
        background: #eee;
        color: #777;
      }
      .status-badge.badge-disconnected {
        background: #eee;
        color: #666;
      }
      .status-badge.badge-pending-test {
        background: #e6f0ff;
        color: #0a5fd6;
      }
      .status-badge.badge-connected {
        background: #e3f7ee;
        color: #0a7;
      }
      .status-badge.badge-error {
        background: #fdeaea;
        color: #c33;
      }
      .quick-toggle {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.85rem;
        white-space: nowrap;
      }
      .sync-stats {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
      }
      .sync-stats .bad {
        color: #c33;
        font-weight: 500;
      }
      .mono {
        font-family: ui-monospace, monospace;
        font-size: 0.85rem;
      }
      .wrap {
        word-break: break-all;
      }
      .provider-body {
        margin-top: 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
      }
      .provider-body label span {
        display: block;
        font-weight: 500;
        margin-bottom: 0.25rem;
      }
      .provider-body input[type='text'],
      .provider-body textarea {
        width: 100%;
        max-width: 640px;
        padding: 0.5rem;
      }
      .chk {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }
      .btn-row {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
      }
      .webhook-box {
        padding: 0.75rem;
        background: var(--soft-bg, #f6f7f9);
        border-radius: 6px;
      }
      .status-row .ok {
        color: #0a7;
        margin-left: 0.5rem;
      }
      .status-row .bad {
        color: #c33;
        margin-left: 0.5rem;
      }
      .inline-input {
        width: 100%;
        max-width: 280px;
      }
      .inline-select {
        min-width: 220px;
        padding: 0.35rem;
      }
      .event-list {
        list-style: none;
        padding: 0;
        margin: 0;
      }
      .event-list li {
        padding: 0.35rem 0;
        border-bottom: 1px solid #eee;
        font-size: 0.9rem;
      }
      .event-list li.bad {
        color: #a33;
      }
      .err {
        display: block;
        font-size: 0.85rem;
      }
      h4 {
        margin: 1rem 0 0.25rem 0;
      }
    `,
  ],
})
export class DeliveryIntegrationsSettingsComponent implements OnInit {
  private readonly api = inject(ApiService);

  loading = signal(false);
  saving = signal(false);
  savingMappings = signal(false);
  testing = signal(false);
  eventsLoading = signal(false);
  message = signal('');
  catalog = signal<DeliveryProviderCatalogRow[]>([]);
  integrations = signal<DeliveryIntegrationPublic[]>([]);
  products = signal<Product[]>([]);

  expanded = signal<string | null>(null);

  tenantName = computed(() => this.integrations()[0]?.tenant_name || '');

  draftEnabled: Record<string, boolean> = {};
  draftStoreId: Record<string, string> = {};
  draftCredentialsJson: Record<string, string> = {};
  mappingDraft: Record<string, DeliveryCatalogMappingRow[]> = {};
  events: Record<string, DeliveryIntegrationEventRow[]> = {};

  mergedRows(): Array<{
    provider_key: string;
    display_name: string;
    integration?: DeliveryIntegrationPublic;
  }> {
    const ints = this.integrations();
    return this.catalog().map((c) => ({
      provider_key: c.provider_key,
      display_name: c.display_name,
      integration: ints.find((i) => i.provider_key === c.provider_key),
    }));
  }

  credentialsPlaceholder(): string {
    return '{"api_key":"your-key"}';
  }

  badgeKey(row: { integration?: DeliveryIntegrationPublic }): string {
    if (!row.integration) return 'SETTINGS.DELIVERY_INTEGRATIONS_BADGE_NOT_CONFIGURED';
    return BADGE_TRANSLATION_KEY[row.integration.status_badge];
  }

  badgeClass(row: { integration?: DeliveryIntegrationPublic }): string {
    if (!row.integration) return 'badge-not-configured';
    return 'badge-' + row.integration.status_badge.replace(/_/g, '-');
  }

  providerInitial(displayName: string): string {
    return (displayName || '?').trim().charAt(0).toUpperCase();
  }

  providerIconPath(providerKey: string): string | null {
    return PROVIDER_BRAND[providerKey]?.path ?? null;
  }

  providerColor(providerKey: string): string {
    const brand = PROVIDER_BRAND[providerKey];
    if (brand) return brand.color;
    let hash = 0;
    for (let i = 0; i < providerKey.length; i++) {
      hash = (hash * 31 + providerKey.charCodeAt(i)) >>> 0;
    }
    return BRAND_PALETTE[hash % BRAND_PALETTE.length];
  }

  quickToggle(row: { provider_key: string; integration?: DeliveryIntegrationPublic }): void {
    if (!row.integration?.id) return;
    this.draftEnabled[row.provider_key] = !this.draftEnabled[row.provider_key];
    this.save(row);
  }

  ngOnInit(): void {
    this.reloadAll();
    this.api.getProducts().subscribe({
      next: (p) => this.products.set(p),
      error: () => this.products.set([]),
    });
  }

  reloadAll(): void {
    this.loading.set(true);
    this.message.set('');
    this.api.getDeliveryIntegrationCatalog().subscribe({
      next: (cat) => {
        this.catalog.set(cat);
        this.api.getDeliveryIntegrations().subscribe({
          next: (ints) => {
            this.integrations.set(ints);
            this.seedDrafts();
            this.loading.set(false);
          },
          error: () => {
            this.loading.set(false);
            this.message.set('Could not load integrations.');
          },
        });
      },
      error: () => {
        this.loading.set(false);
        this.message.set('Could not load provider catalog.');
      },
    });
  }

  private seedDrafts(): void {
    const ints = this.integrations();
    for (const c of this.catalog()) {
      const integ = ints.find((i) => i.provider_key === c.provider_key);
      this.draftEnabled[c.provider_key] = integ?.enabled ?? false;
      this.draftStoreId[c.provider_key] = integ?.external_store_id ?? '';
      this.draftCredentialsJson[c.provider_key] = integ?.credentials_configured
        ? '{"api_key":"••••"}'
        : '{"api_key":""}';
    }
  }

  toggleExpand(pk: string): void {
    if (this.expanded() === pk) {
      this.expanded.set(null);
      return;
    }
    this.expanded.set(pk);
    const row = this.mergedRows().find((r) => r.provider_key === pk);
    if (row?.integration?.id) {
      this.loadMappings(row);
      this.loadEvents(row);
    }
  }

  save(row: { provider_key: string; integration?: DeliveryIntegrationPublic }): void {
    let creds: Record<string, unknown> | undefined;
    const raw = (this.draftCredentialsJson[row.provider_key] || '').trim();
    if (raw && !raw.includes('••••')) {
      try {
        creds = JSON.parse(raw) as Record<string, unknown>;
      } catch {
        this.message.set('Invalid JSON in credentials.');
        return;
      }
    }
    this.saving.set(true);
    this.message.set('');
    this.api
      .upsertDeliveryIntegration({
        provider_key: row.provider_key,
        enabled: !!this.draftEnabled[row.provider_key],
        external_store_id: this.draftStoreId[row.provider_key]?.trim() || null,
        credentials: creds,
      })
      .subscribe({
        next: () => {
          this.saving.set(false);
          this.reloadAll();
        },
        error: () => {
          this.saving.set(false);
          this.message.set('Save failed.');
        },
      });
  }

  runTest(row: { provider_key: string; integration?: DeliveryIntegrationPublic }): void {
    const id = row.integration?.id;
    if (!id) return;
    this.testing.set(true);
    this.message.set('');
    this.api.testDeliveryIntegration(id).subscribe({
      next: (r) => {
        this.testing.set(false);
        this.message.set(r.message || '');
        this.reloadAll();
      },
      error: () => {
        this.testing.set(false);
        this.message.set('Test failed.');
      },
    });
  }

  copyUrl(integration: DeliveryIntegrationPublic): void {
    const url = integration.webhook_url_hint;
    void navigator.clipboard.writeText(url).then(
      () => this.message.set('Copied.'),
      () => this.message.set('Could not copy.'),
    );
  }

  loadMappings(row: { provider_key: string; integration?: DeliveryIntegrationPublic }): void {
    const id = row.integration?.id;
    if (!id) return;
    this.api.getDeliveryMappings(id).subscribe({
      next: (list) => {
        this.mappingDraft[row.provider_key] = list.length
          ? [...list]
          : [{ external_item_id: '', product_id: null }];
      },
      error: () => {
        this.mappingDraft[row.provider_key] = [{ external_item_id: '', product_id: null }];
      },
    });
  }

  loadEvents(row: { provider_key: string; integration?: DeliveryIntegrationPublic }): void {
    const id = row.integration?.id;
    if (!id) return;
    this.eventsLoading.set(true);
    this.api.getDeliveryIntegrationEvents(id, 30).subscribe({
      next: (evs) => {
        this.events[row.provider_key] = evs;
        this.eventsLoading.set(false);
      },
      error: () => {
        this.events[row.provider_key] = [];
        this.eventsLoading.set(false);
      },
    });
  }

  addMapping(row: { provider_key: string }): void {
    const list = this.mappingDraft[row.provider_key] || [];
    list.push({ external_item_id: '', product_id: null });
    this.mappingDraft[row.provider_key] = list;
  }

  removeMapping(row: { provider_key: string }, index: number): void {
    const list = [...(this.mappingDraft[row.provider_key] || [])];
    list.splice(index, 1);
    this.mappingDraft[row.provider_key] = list.length
      ? list
      : [{ external_item_id: '', product_id: null }];
  }

  saveMappings(row: { provider_key: string; integration?: DeliveryIntegrationPublic }): void {
    const id = row.integration?.id;
    if (!id) return;
    const raw = this.mappingDraft[row.provider_key] || [];
    const cleaned = raw
      .filter((m) => (m.external_item_id || '').trim())
      .map((m) => ({
        external_item_id: m.external_item_id.trim(),
        product_id: m.product_id,
        notes: m.notes ?? null,
      }));
    this.savingMappings.set(true);
    this.api.putDeliveryMappings(id, cleaned).subscribe({
      next: () => {
        this.savingMappings.set(false);
        this.loadMappings(row);
        this.loadEvents(row);
      },
      error: () => {
        this.savingMappings.set(false);
        this.message.set('Could not save mappings.');
      },
    });
  }
}
