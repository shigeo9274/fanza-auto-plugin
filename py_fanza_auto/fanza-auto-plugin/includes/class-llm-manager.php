<?php
/**
 * LLM Manager Class for FANZA Auto Plugin
 * 
 * This class handles AI-powered content generation including:
 * - Introduction text generation from descriptions
 * - SEO-optimized title generation
 * - Content enhancement using various LLM APIs
 * 
 * @package FANZAAuto
 * @since 1.0.28
 */

namespace FANZAAuto;

class LLM_Manager {
    
    /**
     * LLM API configuration
     */
    private $api_config = array();
    
    /**
     * Supported LLM providers
     */
    private $supported_providers = array(
        'openai' => 'OpenAI GPT',
        'anthropic' => 'Anthropic Claude',
        'google' => 'Google Gemini',
        'local' => 'Local LLM (Ollama)'
    );
    
    /**
     * Constructor
     */
    public function __construct() {
        $this->init_api_config();
    }
    
    /**
     * Initialize API configuration
     */
    private function init_api_config() {
        $this->api_config = array(
            'provider' => get_option('fanza_auto_llm_provider', 'openai'),
            'openai_api_key' => get_option('fanza_auto_openai_api_key', ''),
            'openai_model' => get_option('fanza_auto_openai_model', 'gpt-4'),
            'anthropic_api_key' => get_option('fanza_auto_anthropic_api_key', ''),
            'anthropic_model' => get_option('fanza_auto_anthropic_model', 'claude-3-sonnet'),
            'google_api_key' => get_option('fanza_auto_google_api_key', ''),
            'local_endpoint' => get_option('fanza_auto_local_endpoint', 'http://localhost:11434'),
            'local_model' => get_option('fanza_auto_local_model', 'llama2'),
            'max_tokens' => get_option('fanza_auto_max_tokens', 1000),
            'temperature' => get_option('fanza_auto_temperature', 0.7)
        );
    }
    
    /**
     * Generate introduction text from description
     * 
     * @param string $description Original description text
     * @param array $metadata Additional metadata (title, genre, actress, etc.)
     * @return string Generated introduction text
     */
    public function generate_introduction($description, $metadata = array()) {
        $prompt = $this->build_introduction_prompt($description, $metadata);
        return $this->call_llm_api($prompt);
    }
    
    /**
     * Generate SEO-optimized title
     * 
     * @param string $original_title Original title
     * @param array $metadata Additional metadata
     * @return string SEO-optimized title
     */
    public function generate_seo_title($original_title, $metadata = array()) {
        $prompt = $this->build_seo_title_prompt($original_title, $metadata);
        return $this->call_llm_api($prompt);
    }
    
    /**
     * Generate enhanced content
     * 
     * @param string $content Original content
     * @param array $metadata Additional metadata
     * @return string Enhanced content
     */
    public function generate_enhanced_content($content, $metadata = array()) {
        $prompt = $this->build_enhancement_prompt($content, $metadata);
        return $this->call_llm_api($prompt);
    }
    
    /**
     * Build introduction generation prompt
     */
    private function build_introduction_prompt($description, $metadata) {
        $context = $this->build_metadata_context($metadata);
        
        return "以下の作品の説明文を基に、魅力的で読者を引き込む紹介文を生成してください。

作品情報：
{$context}

説明文：
{$description}

要求事項：
1. 200-300文字程度の読みやすい文章
2. 作品の魅力を効果的に伝える
3. 自然で自然体な日本語
4. 過度に露骨な表現は避ける
5. 読者の興味を引く書き出し
6. 適切な改行と読みやすさ

生成された紹介文のみを返してください。";
    }
    
    /**
     * Build SEO title generation prompt
     */
    private function build_seo_title_prompt($original_title, $metadata) {
        $context = $this->build_metadata_context($metadata);
        
        return "以下の作品のタイトルを、SEOに効果的で検索されやすいタイトルに最適化してください。

作品情報：
{$context}

元のタイトル：
{$original_title}

要求事項：
1. 30-50文字程度
2. 検索キーワードを含む
3. クリック率を上げる魅力的な表現
4. 作品の内容を正確に表現
5. 過度に露骨な表現は避ける
6. 自然で読みやすい日本語

最適化されたタイトルのみを返してください。";
    }
    
    /**
     * Build content enhancement prompt
     */
    private function build_enhancement_prompt($content, $metadata) {
        $context = $this->build_metadata_context($metadata);
        
        return "以下の作品のコンテンツを、より魅力的で読みやすい内容に改善してください。

作品情報：
{$context}

元のコンテンツ：
{$content}

要求事項：
1. 文章の流れを改善
2. 読みやすさを向上
3. 作品の魅力を効果的に表現
4. 適切な段落分け
5. 自然で自然体な日本語
6. 過度に露骨な表現は避ける

改善されたコンテンツのみを返してください。";
    }
    
    /**
     * Build metadata context string
     */
    private function build_metadata_context($metadata) {
        $context = '';
        
        if (!empty($metadata['title'])) {
            $context .= "タイトル: {$metadata['title']}\n";
        }
        if (!empty($metadata['genre'])) {
            $context .= "ジャンル: {$metadata['genre']}\n";
        }
        if (!empty($metadata['actress'])) {
            $context .= "女優: {$metadata['actress']}\n";
        }
        if (!empty($metadata['maker'])) {
            $context .= "メーカー: {$metadata['maker']}\n";
        }
        if (!empty($metadata['series'])) {
            $context .= "シリーズ: {$metadata['series']}\n";
        }
        if (!empty($metadata['director'])) {
            $context .= "監督: {$metadata['director']}\n";
        }
        if (!empty($metadata['date'])) {
            $context .= "発売日: {$metadata['date']}\n";
        }
        
        return $context;
    }
    
    /**
     * Call LLM API based on configured provider
     */
    private function call_llm_api($prompt) {
        $provider = $this->api_config['provider'];
        
        switch ($provider) {
            case 'openai':
                return $this->call_openai_api($prompt);
            case 'anthropic':
                return $this->call_anthropic_api($prompt);
            case 'google':
                return $this->call_google_api($prompt);
            case 'local':
                return $this->call_local_api($prompt);
            default:
                return $this->call_openai_api($prompt);
        }
    }
    
    /**
     * Call OpenAI API
     */
    private function call_openai_api($prompt) {
        if (empty($this->api_config['openai_api_key'])) {
            return $this->get_error_response('OpenAI API key not configured');
        }
        
        $url = 'https://api.openai.com/v1/chat/completions';
        $headers = array(
            'Authorization: Bearer ' . $this->api_config['openai_api_key'],
            'Content-Type: application/json'
        );
        
        $data = array(
            'model' => $this->api_config['openai_model'],
            'messages' => array(
                array(
                    'role' => 'system',
                    'content' => 'あなたは日本語のコンテンツ作成の専門家です。'
                ),
                array(
                    'role' => 'user',
                    'content' => $prompt
                )
            ),
            'max_tokens' => $this->api_config['max_tokens'],
            'temperature' => $this->api_config['temperature']
        );
        
        return $this->make_api_request($url, $headers, $data);
    }
    
    /**
     * Call Anthropic API
     */
    private function call_anthropic_api($prompt) {
        if (empty($this->api_config['anthropic_api_key'])) {
            return $this->get_error_response('Anthropic API key not configured');
        }
        
        $url = 'https://api.anthropic.com/v1/messages';
        $headers = array(
            'x-api-key: ' . $this->api_config['anthropic_api_key'],
            'Content-Type: application/json',
            'anthropic-version: 2023-06-01'
        );
        
        $data = array(
            'model' => $this->api_config['anthropic_model'],
            'max_tokens' => $this->api_config['max_tokens'],
            'messages' => array(
                array(
                    'role' => 'user',
                    'content' => $prompt
                )
            )
        );
        
        return $this->make_api_request($url, $headers, $data);
    }
    
    /**
     * Call Google Gemini API
     */
    private function call_google_api($prompt) {
        if (empty($this->api_config['google_api_key'])) {
            return $this->get_error_response('Google API key not configured');
        }
        
        $url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=' . $this->api_config['google_api_key'];
        
        $data = array(
            'contents' => array(
                array(
                    'parts' => array(
                        array(
                            'text' => $prompt
                        )
                    )
                )
            ),
            'generationConfig' => array(
                'maxOutputTokens' => $this->api_config['max_tokens'],
                'temperature' => $this->api_config['temperature']
            )
        );
        
        return $this->make_api_request($url, array('Content-Type: application/json'), $data);
    }
    
    /**
     * Call Local LLM API (Ollama)
     */
    private function call_local_api($prompt) {
        $url = $this->api_config['local_endpoint'] . '/api/generate';
        
        $data = array(
            'model' => $this->api_config['local_model'],
            'prompt' => $prompt,
            'stream' => false,
            'options' => array(
                'num_predict' => $this->api_config['max_tokens'],
                'temperature' => $this->api_config['temperature']
            )
        );
        
        return $this->make_api_request($url, array('Content-Type: application/json'), $data);
    }
    
    /**
     * Make API request
     */
    private function make_api_request($url, $headers, $data) {
        $ch = curl_init();
        
        curl_setopt_array($ch, array(
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST => true,
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_POSTFIELDS => json_encode($data),
            CURLOPT_TIMEOUT => 30,
            CURLOPT_SSL_VERIFYPEER => false
        ));
        
        $response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);
        
        if ($error) {
            return $this->get_error_response('cURL Error: ' . $error);
        }
        
        if ($http_code !== 200) {
            return $this->get_error_response('API Error: HTTP ' . $http_code);
        }
        
        return $this->parse_api_response($response);
    }
    
    /**
     * Parse API response based on provider
     */
    private function parse_api_response($response) {
        $provider = $this->api_config['provider'];
        $data = json_decode($response, true);
        
        if (!$data) {
            return $this->get_error_response('Invalid API response');
        }
        
        switch ($provider) {
            case 'openai':
                return isset($data['choices'][0]['message']['content']) 
                    ? trim($data['choices'][0]['message']['content']) 
                    : $this->get_error_response('OpenAI response format error');
                    
            case 'anthropic':
                return isset($data['content'][0]['text']) 
                    ? trim($data['content'][0]['text']) 
                    : $this->get_error_response('Anthropic response format error');
                    
            case 'google':
                return isset($data['candidates'][0]['content']['parts'][0]['text']) 
                    ? trim($data['candidates'][0]['content']['parts'][0]['text']) 
                    : $this->get_error_response('Google response format error');
                    
            case 'local':
                return isset($data['response']) 
                    ? trim($data['response']) 
                    : $this->get_error_response('Local LLM response format error');
                    
            default:
                return $this->get_error_response('Unknown provider');
        }
    }
    
    /**
     * Get error response
     */
    private function get_error_response($message) {
        return '<!-- LLM Error: ' . esc_html($message) . ' -->';
    }
    
    /**
     * Get supported providers
     */
    public function get_supported_providers() {
        return $this->supported_providers;
    }
    
    /**
     * Get current configuration
     */
    public function get_config() {
        return $this->api_config;
    }
    
    /**
     * Update configuration
     */
    public function update_config($new_config) {
        $this->api_config = array_merge($this->api_config, $new_config);
        
        // Save to WordPress options
        foreach ($new_config as $key => $value) {
            update_option('fanza_auto_' . $key, $value);
        }
    }
    
    /**
     * Test API connection
     */
    public function test_connection() {
        $test_prompt = 'こんにちは。テストメッセージです。';
        $response = $this->call_llm_api($test_prompt);
        
        return !str_contains($response, 'LLM Error');
    }
}

