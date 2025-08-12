<?php
/**
 * LLM Admin Class for FANZA Auto Plugin
 * 
 * This class handles the admin interface for LLM settings
 * 
 * @package FANZAAuto
 * @since 1.0.28
 */

namespace FANZAAuto;

class LLM_Admin {
    
    /**
     * LLM Manager instance
     */
    private $llm_manager;
    
    /**
     * Constructor
     */
    public function __construct() {
        $this->llm_manager = new LLM_Manager();
        $this->init_hooks();
    }
    
    /**
     * Initialize WordPress hooks
     */
    private function init_hooks() {
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_init', array($this, 'handle_form_submission'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_admin_scripts'));
    }
    
    /**
     * Add admin menu
     */
    public function add_admin_menu() {
        add_submenu_page(
            'fanza-auto-plugin-menu',
            'LLM設定', 
            'LLM設定', 
            'manage_options', 
            'fanza-auto-llm-settings', 
            array($this, 'render_admin_page')
        );
    }
    
    /**
     * Enqueue admin scripts and styles
     */
    public function enqueue_admin_scripts($hook) {
        if ($hook !== 'fanza-auto_page_fanza-auto-llm-settings') {
            return;
        }
        
        wp_enqueue_script('jquery');
        wp_enqueue_style('wp-admin');
    }
    
    /**
     * Handle form submission
     */
    public function handle_form_submission() {
        if (!isset($_POST['fanza_auto_llm_submit'])) {
            return;
        }
        
        if (!wp_verify_nonce($_POST['fanza_auto_llm_nonce'], 'fanza_auto_llm_action')) {
            wp_die('セキュリティチェックに失敗しました。');
        }
        
        $config = array(
            'provider' => sanitize_text_field($_POST['llm_provider']),
            'openai_api_key' => sanitize_text_field($_POST['openai_api_key']),
            'openai_model' => sanitize_text_field($_POST['openai_model']),
            'anthropic_api_key' => sanitize_text_field($_POST['anthropic_api_key']),
            'anthropic_model' => sanitize_text_field($_POST['anthropic_model']),
            'google_api_key' => sanitize_text_field($_POST['google_api_key']),
            'local_endpoint' => sanitize_text_field($_POST['local_endpoint']),
            'local_model' => sanitize_text_field($_POST['local_model']),
            'max_tokens' => intval($_POST['max_tokens']),
            'temperature' => floatval($_POST['temperature'])
        );
        
        $this->llm_manager->update_config($config);
        
        // Test connection if requested
        if (isset($_POST['test_connection'])) {
            $test_result = $this->llm_manager->test_connection();
            if ($test_result) {
                add_action('admin_notices', array($this, 'show_success_notice'));
            } else {
                add_action('admin_notices', array($this, 'show_error_notice'));
            }
        } else {
            add_action('admin_notices', array($this, 'show_success_notice'));
        }
    }
    
    /**
     * Show success notice
     */
    public function show_success_notice() {
        echo '<div class="notice notice-success is-dismissible"><p>LLM設定が保存されました。</p></div>';
    }
    
    /**
     * Show error notice
     */
    public function show_error_notice() {
        echo '<div class="notice notice-error is-dismissible"><p>LLM API接続テストに失敗しました。設定を確認してください。</p></div>';
    }
    
    /**
     * Render admin page
     */
    public function render_admin_page() {
        $config = $this->llm_manager->get_config();
        $providers = $this->llm_manager->get_supported_providers();
        ?>
        <div class="wrap">
            <h1>FANZA Auto Plugin - LLM設定</h1>
            
            <form method="post" action="">
                <?php wp_nonce_field('fanza_auto_llm_action', 'fanza_auto_llm_nonce'); ?>
                
                <table class="form-table">
                    <tr>
                        <th scope="row">
                            <label for="llm_provider">LLMプロバイダー</label>
                        </th>
                        <td>
                            <select name="llm_provider" id="llm_provider">
                                <?php foreach ($providers as $key => $name): ?>
                                    <option value="<?php echo esc_attr($key); ?>" <?php selected($config['provider'], $key); ?>>
                                        <?php echo esc_html($name); ?>
                                    </option>
                                <?php endforeach; ?>
                            </select>
                            <p class="description">使用するLLMサービスを選択してください。</p>
                        </td>
                    </tr>
                    
                    <!-- OpenAI Settings -->
                    <tr class="provider-settings openai-settings">
                        <th scope="row">
                            <label for="openai_api_key">OpenAI API Key</label>
                        </th>
                        <td>
                            <input type="password" name="openai_api_key" id="openai_api_key" 
                                   value="<?php echo esc_attr($config['openai_api_key']); ?>" class="regular-text" />
                            <p class="description">OpenAI APIキーを入力してください。</p>
                        </td>
                    </tr>
                    
                    <tr class="provider-settings openai-settings">
                        <th scope="row">
                            <label for="openai_model">OpenAI モデル</label>
                        </th>
                        <td>
                            <select name="openai_model" id="openai_model">
                                <option value="gpt-4" <?php selected($config['openai_model'], 'gpt-4'); ?>>GPT-4</option>
                                <option value="gpt-4-turbo" <?php selected($config['openai_model'], 'gpt-4-turbo'); ?>>GPT-4 Turbo</option>
                                <option value="gpt-3.5-turbo" <?php selected($config['openai_model'], 'gpt-3.5-turbo'); ?>>GPT-3.5 Turbo</option>
                            </select>
                        </td>
                    </tr>
                    
                    <!-- Anthropic Settings -->
                    <tr class="provider-settings anthropic-settings">
                        <th scope="row">
                            <label for="anthropic_api_key">Anthropic API Key</label>
                        </th>
                        <td>
                            <input type="password" name="anthropic_api_key" id="anthropic_api_key" 
                                   value="<?php echo esc_attr($config['anthropic_api_key']); ?>" class="regular-text" />
                            <p class="description">Anthropic APIキーを入力してください。</p>
                        </td>
                    </tr>
                    
                    <tr class="provider-settings anthropic-settings">
                        <th scope="row">
                            <label for="anthropic_model">Anthropic モデル</label>
                        </th>
                        <td>
                            <select name="anthropic_model" id="anthropic_model">
                                <option value="claude-3-opus" <?php selected($config['anthropic_model'], 'claude-3-opus'); ?>>Claude 3 Opus</option>
                                <option value="claude-3-sonnet" <?php selected($config['anthropic_model'], 'claude-3-sonnet'); ?>>Claude 3 Sonnet</option>
                                <option value="claude-3-haiku" <?php selected($config['anthropic_model'], 'claude-3-haiku'); ?>>Claude 3 Haiku</option>
                            </select>
                        </td>
                    </tr>
                    
                    <!-- Google Settings -->
                    <tr class="provider-settings google-settings">
                        <th scope="row">
                            <label for="google_api_key">Google API Key</label>
                        </th>
                        <td>
                            <input type="password" name="google_api_key" id="google_api_key" 
                                   value="<?php echo esc_attr($config['google_api_key']); ?>" class="regular-text" />
                            <p class="description">Google AI Studio APIキーを入力してください。</p>
                        </td>
                    </tr>
                    
                    <!-- Local LLM Settings -->
                    <tr class="provider-settings local-settings">
                        <th scope="row">
                            <label for="local_endpoint">ローカルLLM エンドポイント</label>
                        </th>
                        <td>
                            <input type="url" name="local_endpoint" id="local_endpoint" 
                                   value="<?php echo esc_attr($config['local_endpoint']); ?>" class="regular-text" />
                            <p class="description">OllamaなどのローカルLLMのエンドポイントURLを入力してください。</p>
                        </td>
                    </tr>
                    
                    <tr class="provider-settings local-settings">
                        <th scope="row">
                            <label for="local_model">ローカルLLM モデル</label>
                        </th>
                        <td>
                            <input type="text" name="local_model" id="local_model" 
                                   value="<?php echo esc_attr($config['local_model']); ?>" class="regular-text" />
                            <p class="description">使用するローカルモデル名を入力してください（例：llama2, mistral）。</p>
                        </td>
                    </tr>
                    
                    <!-- General Settings -->
                    <tr>
                        <th scope="row">
                            <label for="max_tokens">最大トークン数</label>
                        </th>
                        <td>
                            <input type="number" name="max_tokens" id="max_tokens" 
                                   value="<?php echo esc_attr($config['max_tokens']); ?>" min="100" max="4000" />
                            <p class="description">生成されるテキストの最大長を指定してください。</p>
                        </td>
                    </tr>
                    
                    <tr>
                        <th scope="row">
                            <label for="temperature">温度（創造性）</label>
                        </th>
                        <td>
                            <input type="range" name="temperature" id="temperature" 
                                   value="<?php echo esc_attr($config['temperature']); ?>" min="0.0" max="2.0" step="0.1" />
                            <span id="temperature_value"><?php echo esc_html($config['temperature']); ?></span>
                            <p class="description">低い値：一貫性重視、高い値：創造性重視</p>
                        </td>
                    </tr>
                </table>
                
                <p class="submit">
                    <input type="submit" name="fanza_auto_llm_submit" class="button-primary" value="設定を保存" />
                    <input type="submit" name="test_connection" class="button-secondary" value="接続テスト" />
                </p>
            </form>
            
            <hr>
            
            <h2>使用方法</h2>
            <div class="card">
                <h3>紹介文の自動生成</h3>
                <p>投稿設定で以下の変数タグを使用することで、LLMによる自動生成が有効になります：</p>
                <ul>
                    <li><code>[llm_intro]</code> - 説明文から魅力的な紹介文を生成</li>
                    <li><code>[llm_seo_title]</code> - SEO最適化されたタイトルを生成</li>
                    <li><code>[llm_enhance]</code> - 既存コンテンツを改善</li>
                </ul>
                
                <h3>例</h3>
                <p><strong>タイトルテンプレート：</strong> <code>[llm_seo_title]</code></p>
                <p><strong>本文テンプレート：</strong> <code>[llm_intro]</code></p>
            </div>
            
            <div class="card">
                <h3>対応LLMサービス</h3>
                <ul>
                    <li><strong>OpenAI GPT:</strong> GPT-4, GPT-3.5 Turbo</li>
                    <li><strong>Anthropic Claude:</strong> Claude 3 Opus, Sonnet, Haiku</li>
                    <li><strong>Google Gemini:</strong> Gemini Pro</li>
                    <li><strong>ローカルLLM:</strong> Ollama対応モデル</li>
                </ul>
            </div>
        </div>
        
        <style>
        .provider-settings {
            display: none;
        }
        .provider-settings.active {
            display: table-row;
        }
        .card {
            background: #fff;
            border: 1px solid #ccd0d4;
            border-radius: 4px;
            padding: 20px;
            margin: 20px 0;
        }
        .card h3 {
            margin-top: 0;
        }
        </style>
        
        <script>
        jQuery(document).ready(function($) {
            // Show/hide provider-specific settings
            function toggleProviderSettings() {
                var provider = $('#llm_provider').val();
                $('.provider-settings').removeClass('active');
                $('.' + provider + '-settings').addClass('active');
            }
            
            $('#llm_provider').on('change', toggleProviderSettings);
            toggleProviderSettings();
            
            // Temperature slider
            $('#temperature').on('input', function() {
                $('#temperature_value').text($(this).val());
            });
        });
        </script>
        <?php
    }
}

