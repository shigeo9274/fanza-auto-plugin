<?php
/*
  Plugin Name: FANZA Auto Plugin
  Plugin URI:  https://auto-affi.com
  Description: 【FANZAアフィリエイト記事大量投稿プラグイン】 このプラグインはDMM WEB APIを利用して検索条件を設定し自動投稿・放置運用を実現するプラグインです。
  Version: 1.0.28
  Author: AUTO-AFFI
  Author URI: https://auto-affi.com
 */

namespace FANZAAuto;

class FANZAAutoPlugin {
    const PLUGIN_NAME  = 'fanza-auto-plugin';
    const NONCE_ACTION = self::PLUGIN_NAME . '-nonce-action';
    const NONCE_FIELD  = self::PLUGIN_NAME . '-nonce-field';
    const DB_PREFIX    = self::PLUGIN_NAME . '_';

    // Eyecatch
    public $eyecatch_ary = array(
        'package'=>'パッケージ画像を利用',
        'sample'=>'サンプル画像:自動選択',
        '1'=>'サンプル画像:1枚目',
        '2'=>'サンプル画像:2枚目',
        '3'=>'サンプル画像:3枚目',
        '4'=>'サンプル画像:4枚目',
        '99'=>'サンプル画像:最後',
        'none'=>'指定なし',
    );

    // Movie small - size
    public $movie_small_ary = array(
        '476'=>'476×306',
        '560'=>'560×360',
        '600'=>'600×500',
        '644'=>'644×414',
        '720'=>'720×480',
        'auto'=>'auto',
    );

    // Movie large - Poster image
    public $poster_ary = array(
        'package'=>'パッケージ画像を利用',
        'sample'=>'サンプル画像:自動選択',
        'none'=>'指定なし',
    );

    // Category / Tag
    public $category_ary = array(
        'jan'=>'ジャンル',
        'act'=>'女優',
        'director'=>'監督',
        'seri'=>'シリーズ名',
        'maker'=>'メーカー',
        'label'=>'レーベル',
        'manufacture'=>'出版社',
        'author'=>'作者',
    );

    public $sort_ary = array(
        'rank'=>'人気順',
        'date'=>'新着順',
        'review'=>'評価順',
        'price'=>'価格が高い順',
    );

    public $article_ary = array(
        ''=>'',
        'actress'=>'女優',
        'author'=>'作者',
        'genre'=>'ジャンル',
        'series'=>'シリーズ',
        'maker'=>'メーカー',
    );

    // post_status
    public $post_status_ary = array(
        'publish'=>'公開（publish）',
        'draft'=>'下書き（draft）',
    );

    // Auto exe hour
    public $hour_ary = array(
        'h00'=>'00時台',
        'h01'=>'01時台',
        'h02'=>'02時台',
        'h03'=>'03時台',
        'h04'=>'04時台',
        'h05'=>'05時台',
        'h06'=>'06時台',
        'h07'=>'07時台',
        'h08'=>'08時台',
        'h09'=>'09時台',
        'h10'=>'10時台',
        'h11'=>'11時台',
        'h12'=>'12時台',
        'h13'=>'13時台',
        'h14'=>'14時台',
        'h15'=>'15時台',
        'h16'=>'16時台',
        'h17'=>'17時台',
        'h18'=>'18時台',
        'h19'=>'19時台',
        'h20'=>'20時台',
        'h21'=>'21時台',
        'h22'=>'22時台',
        'h23'=>'23時台',
    );

    public $complete='';
    public $contents_array = array();
    public $floor_array = array();
    public $auto_log = ABSPATH . 'wp-content/plugins/'.self::PLUGIN_NAME.'/fanza-auto.log';
    
    // LLM Manager instance
    private $llm_manager;
        
    // Constructor
    public function __construct() {
        ini_set('max_execution_time',900);

        require_once ABSPATH . 'wp-content/plugins/'.self::PLUGIN_NAME.'/includes/action-scheduler-trunk/action-scheduler.php';
        require_once ABSPATH . 'wp-content/plugins/'.self::PLUGIN_NAME.'/includes/class-llm-manager.php';
        require_once ABSPATH . 'wp-content/plugins/'.self::PLUGIN_NAME.'/includes/class-llm-admin.php';
        
        // register_uninstall_hook(__FILE__, 'FANZAAutoPlugin::uninstall');

        // Initialize LLM functionality
        $this->init_llm();
        
        // Set default LLM options if not exists
        $this->set_default_llm_options();

        // add menu
        add_action('admin_menu', [$this, 'set_plugin_menu']);

        // callback function
        add_action('admin_init', [$this, 'save_config']);
        add_action('admin_init', [$this, 'save_submit']);
        add_action('admin_init', [$this, 'printArray']);
        add_action('admin_init', [$this, 'quick_exe']);
        add_action('admin_init', [$this, 'hour_submit']);

        add_action('fanza_autoA_hook', [$this, 'fanza_autoA']);
        add_action('fanza_autoB_hook', [$this, 'fanza_autoB']);
    }
    
    /**
     * Initialize LLM functionality
     */
    private function init_llm() {
        $this->llm_manager = new LLM_Manager();
        new LLM_Admin();
    }
    
    /**
     * Set default LLM options
     */
    private function set_default_llm_options() {
        $default_options = array(
            'fanza_auto_llm_provider' => 'openai',
            'fanza_auto_openai_model' => 'gpt-4',
            'fanza_auto_anthropic_model' => 'claude-3-sonnet',
            'fanza_auto_local_endpoint' => 'http://localhost:11434',
            'fanza_auto_local_model' => 'llama2',
            'fanza_auto_max_tokens' => 1000,
            'fanza_auto_temperature' => 0.7
        );
        
        foreach ($default_options as $option => $value) {
            if (get_option($option) === false) {
                add_option($option, $value);
            }
        }
    }

    // Uninstall process
    // public static function uninstall() {
	// 	delete_option(self::PLUGIN_NAME);
	// }

    // Admin menu
    function set_plugin_menu() {
        add_menu_page(
            'FANZA Auto', 
            'FANZA Auto', 
            'manage_options', 
            'fanza-auto-plugin-menu', 
            '', 
            'dashicons-format-gallery', 
            99
        );
        add_submenu_page(
            'fanza-auto-plugin-menu',
            '自動実行ON-OFF', 
            '自動実行ON-OFF', 
            'manage_options', 
            'fanza-auto-plugin-menu', 
            [$this,'fanza_auto_set'], 
            // [$this,'show_config_form'], 
            0
        );        

        add_submenu_page(
            'fanza-auto-plugin-menu',
            '投稿設定1', 
            '投稿設定1', 
            'manage_options', 
            'fanza-auto-menu1', 
            [$this,'show_config_form1'], 
            1
        );
        add_submenu_page(
            'fanza-auto-plugin-menu',
            '投稿設定2', 
            '投稿設定2', 
            'manage_options', 
            'fanza-auto-menu2', 
            [$this,'show_config_form2'], 
            2
        );
        add_submenu_page(
            'fanza-auto-plugin-menu',
            '投稿設定3', 
            '投稿設定3', 
            'manage_options', 
            'fanza-auto-menu3', 
            [$this,'show_config_form3'], 
            3
        );
        add_submenu_page(
            'fanza-auto-plugin-menu',
            '投稿設定4', 
            '投稿設定4', 
            'manage_options', 
            'fanza-auto-menu4', 
            [$this,'show_config_form4'], 
            4
        );

        add_submenu_page(
            'fanza-auto-plugin-menu',
            '変数タグ一覧', 
            '変数タグ一覧', 
            'manage_options', 
            'fanza-auto-vartag', 
            [$this,'fanza_auto_vartag'], 
            99
        );


    }

    function auto_process_log($log_str){
        $auto_log_text = "[" . date_i18n("Ymd H:i") . "] " . $log_str. "\n";
        file_put_contents($this->auto_log, $auto_log_text, FILE_APPEND);
    }
    function dump($object){
        echo("<pre>");
        var_dump($object);
        echo("</pre>");
    }

    function post_set_page($set_menu_number){
        $number = "";
        if($set_menu_number != "1") $number = $set_menu_number.'_';
        $template_number = "";
        if($set_menu_number != "1") $template_number = $set_menu_number;

        $api_id          = get_option(self::DB_PREFIX . 'api_id');
        $aff_id          = get_option(self::DB_PREFIX . 'aff_id');
     
        $eye             = get_option(self::DB_PREFIX . $number . 'eye');
        $poster          = get_option(self::DB_PREFIX . $number . 'poster');
        $floor           = get_option(self::DB_PREFIX . $number . 'floor');
        $maximage        = get_option(self::DB_PREFIX . $number . 'maximage');
        $cate_other      = get_option(self::DB_PREFIX . $number . 'cate_other');
        $cate_free       = get_option(self::DB_PREFIX . $number . 'cate_free');
        $tag_other       = get_option(self::DB_PREFIX . $number . 'tag_other');
        $tag_free        = get_option(self::DB_PREFIX . $number . 'tag_free');
        $hits            = get_option(self::DB_PREFIX . $number . 'hits');
        $from_date       = get_option(self::DB_PREFIX . $number . 'from_date');
        $to_date         = get_option(self::DB_PREFIX . $number . 'to_date');
        $keyword         = get_option(self::DB_PREFIX . $number . 'keyword');
        $article_type    = get_option(self::DB_PREFIX . $number . 'article_type');
        $article_id      = get_option(self::DB_PREFIX . $number . 'article_id');
        $sort            = get_option(self::DB_PREFIX . $number . 'sort');
        $output          = get_option(self::DB_PREFIX . $number . 'output');
        $b_word          = get_option(self::DB_PREFIX . $number . 'b_word');
        $b_word2         = get_option(self::DB_PREFIX . $number . 'b_word2');
        $t_title         = get_option(self::DB_PREFIX . $number . 't_title');
        $t_excerpt       = get_option(self::DB_PREFIX . $number . 't_excerpt');
        $cate            = get_option(self::DB_PREFIX . $number . 'cate');
        $tag             = get_option(self::DB_PREFIX . $number . 'tag');
        $ex_cate         = get_option(self::DB_PREFIX . $number . 'ex_cate');
        $ex_tag          = get_option(self::DB_PREFIX . $number . 'ex_tag');
        $b_color         = get_option(self::DB_PREFIX . $number . 'b_color');
        $t_color         = get_option(self::DB_PREFIX . $number . 't_color');
        $b_color2        = get_option(self::DB_PREFIX . $number . 'b_color2');
        $t_color2        = get_option(self::DB_PREFIX . $number . 't_color2');
        $movie_size      = get_option(self::DB_PREFIX . $number . 'movie_size');
        $post_date       = get_option(self::DB_PREFIX . $number . 'post_date');
        $specify_date    = get_option(self::DB_PREFIX . $number . 'specify_date');
        $rand_start_date = get_option(self::DB_PREFIX . $number . 'rand_start_date');
        $rand_end_date   = get_option(self::DB_PREFIX . $number . 'rand_end_date');
        $limited_flag    = get_option(self::DB_PREFIX . $number . 'limited_flag');
        $random_text1    = get_option(self::DB_PREFIX . $number . 'random_text1');
        $random_text2    = get_option(self::DB_PREFIX . $number . 'random_text2');
        $random_text3    = get_option(self::DB_PREFIX . $number . 'random_text3');

        if($b_color == '') $b_color = '#ff0000';
        if($t_color == '') $t_color = '#ffffff';
        if($b_color2 == '') $b_color2 = '#0000ff';
        if($t_color2 == '') $t_color2 = '#ffffff';
        if($b_word == '') $b_word = 'この作品の価格を確認';
        if($b_word2 == '') $b_word2 = '続きの画像はこちら';

        $category = explode('/', $cate);
        $tags = explode('/', $tag);
        $ex_category = explode('/', $ex_cate);
        $ex_tags = explode('/', $ex_tag);

        global $wpdb;
        $table_prefix = $wpdb->prefix;
        $query = "SELECT id FROM {$table_prefix}posts WHERE post_title='FANZAテンプレート".$template_number."' && post_type='post' && post_status='draft' ORDER BY post_date desc limit 1";
        $result = $wpdb->get_results($query, OBJECT);
        $template_id = '';
        foreach ($result as $row) {
            $template_id = $row->id;
        }
        $this->make_floor();
        // カテゴリ表示
        $terms = get_terms( array( 'taxonomy'=>'category', 'get'=>'all' ) );
        $term_tags = get_terms( array( 'taxonomy'=>'post_tag', 'get'=>'all' ) );
        ?>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/css/bootstrap.min.css" integrity="sha384-GJzZqFGwb1QTTN6wy59ffF1BuGJpLSa9DkKMp0DgiMDm4iYMj70gZWKYbI706tWS" crossorigin="anonymous">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.6/umd/popper.min.js" integrity="sha384-wHAiFfRlMFy6i5SRaxvfOCifBUQy1xHdJ/yoi7FRNXMRBu5WHdZYu1hA6ZOblgut" crossorigin="anonymous"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/js/bootstrap.min.js" integrity="sha384-B0UglyR+jN6CkvvICOB2joaf5I4l3gm9GU6Hc1og6Ls7i6U/mkkaduKaBhlAXv9k" crossorigin="anonymous"></script>

        <div class="fanza-auto">
            <h2 class="">FANZA Auto大量投稿プラグイン | 投稿設定<?= $set_menu_number ?></h2>

            <form action="?" method="POST" id="dmm-add-form">
            <?php wp_nonce_field(self::NONCE_ACTION, self::NONCE_FIELD) ?>

        <!-- ================================ -->

        <style>
        .setting th { padding: 5px; background-color: #eee;}
        .setting td { padding: 5px; }
        </style>

        <table border="1" style="border: 15px solid black; border-collapse: collapse; color:white; background-color:black; width:99%; cursor:pointer; ">
        <tr id="collapseSetting" data-toggle="collapse" href="#collapseExample" role="button" aria-expanded="false" aria-controls="collapseExample">
            <td>投稿設定<?= $set_menu_number ?>：初期設定</td>
            <td align="right"><span id="collapse_triangle">▼</span></td>
        </tr>
        </table>

        <div class="collapse" id="collapseExample">
        <table class="setting" border="1" style="width:99%; border: 1px solid black; border-collapse: collapse;">
        <tr><th width="30%">投稿タイトルテンプレート</th><td>
            <input type="text" id="t_title" name="t_title" class="" aria-describedby="b_wordHelpBlock" value="<?= $t_title ?>" size="50" placeholder="標準：[title]" />
        </td></tr>
        <tr><th>投稿本文テンプレート</th><td>

            <?php
                if ($template_id) {
                    $admin_post_url = admin_url('post.php');
                    echo "「FANZAテンプレート".$template_number."」というタイトル名の「下書き保存」記事をテンプレートとして利用します<br>";
                    echo "&nbsp;→[<a href=\"{$admin_post_url}?post={$template_id}&action=edit\" target=\"_blank\">FANZAテンプレート".$template_number."を修正</a>]";
                } else {
                    $admin_new_url = admin_url('post-new.php');
                    echo "「FANZAテンプレート".$template_number."」というタイトル名で「下書き保存」記事を作成してください<br>";
                    echo "&nbsp;→[<a href=\"{$admin_new_url}\" target=\"_blank\">FANZAテンプレート".$template_number."を新規作成</a>]";
                }
                ?>

        </td></tr>
        <tr><th>抜粋（excerpt）欄テンプレート</th><td>
            <input type="text" id="t_excerpt" name="t_excerpt" class="" aria-describedby="b_wordHelpBlock" value="<?= $t_excerpt ?>" size="50" placeholder="標準は空白（カスタマイズ例：[cid] | [comment]）" />
        </td></tr>
        <tr><td colspan="2">
            &nbsp;&nbsp;※各テンプレートに[<a href="<?=  admin_url('admin.php') ?>?page=fanza-auto-vartag" target="_blank">変数タグ</a>]を指定することで、作品別の特定情報を入れることが可能<br>  
        </td></tr>
        <tr><th>アイキャッチ画像の種類</th><td>
            <select name="eye" class="form-select" aria-describedby="eyeHelpBlock">
                                <?php
                                    echo $this->make_option($this->eyecatch_ary, $eye);
                                ?>
            </select>
        </td></tr>
        <tr><th>サンプル画像の表示数（最大）</th><td>
            <input type="number" id="maximage" name="maximage" aria-describedby="" placeholder="0" pattern="^[0-9]+$" min="0" max="30" value="<?= $maximage ?>" />&nbsp;※0：全ての画像を表示
        </td></tr>
        <tr><th>サンプル動画（小）サイズ</th><td>
            <select name="movie_size" class="form-select" aria-describedby="movie_sizeHelpBlock">
                                <?php
                                    echo $this->make_option($this->movie_small_ary, $movie_size);
                                ?>
            </select>
        </td></tr>
        <tr><th>サンプル動画（大）の表示画像</th><td>
            <select name="poster" class="form-select" aria-describedby="eyeHelpBlock">
                                <?php
                                    echo $this->make_option($this->poster_ary, $poster);
                                ?>
            </select>
        </td></tr>
        <tr><th>カテゴリ指定</th><td>
            <?php
                                echo $this->make_cate_check_box($this->category_ary, $category);
            ?>
            <br>
            <input type="checkbox" id="cate_other" name="cate_other" value="1" <?php if($cate_other){echo("checked");} ?> >
            <label for="cate_other">自由記述（複数は「,」区切り）</label>&nbsp;
            <input type="text" id="cate_free" name="cate_free" value="<?= $cate_free ?>"/>
        </td></tr>
        <tr><th>タグ指定</th><td>
            <?php
                                echo $this->make_tag_check_box($this->category_ary, $tags);
            ?>
            <br>
            <input type="checkbox" id="tag_other" name="tag_other" value="1" <?php if($tag_other){echo("checked");} ?> >
            <label for="tag_other">自由記述（複数は「,」区切り）</label>&nbsp;
            <input type="text" id="tag_free" name="tag_free" value="<?= $tag_free ?>"/>
        </td></tr>
        <tr><th>アフィリエイトボタン1</th><td>
            文言
            <input type="text" id="b_word" name="b_word" class="" aria-describedby="b_wordHelpBlock" value="<?= $b_word ?>" size="25" />&nbsp;
            文字色
            <input type="color" id="t_color" name="t_color" class="form-control-color" aria-describedby="t_colorHelpBlock" value="<?= $t_color ?>" />&nbsp;
            背景色
            <input type="color" id="b_color" name="b_color" class="form-control-color" aria-describedby="b_colorHelpBlock" value="<?= $b_color ?>" />&nbsp;
        </td></tr>
        <tr><th>アフィリエイトボタン2</th><td>
            文言
            <input type="text" id="b_word2" name="b_word2" class="" aria-describedby="b_wordHelpBlock" value="<?= $b_word2 ?>" size="25" />&nbsp;
            文字色
            <input type="color" id="t_color2" name="t_color2" class="form-control-color" aria-describedby="t_colorHelpBlock" value="<?= $t_color2 ?>" />&nbsp;
            背景色
            <input type="color" id="b_color2" name="b_color2" class="form-control-color" aria-describedby="b_colorHelpBlock" value="<?= $b_color2 ?>" />&nbsp;
        </td></tr>
        <tr><th>投稿日</th><td>
            <input type="radio" id="p_today" name="post_date" value="p_today" <?php if($post_date=="p_today"){echo("checked");} ?>/><label for="today">本日（実行日）</label><br>

            <input type="radio" id="p_specify" name="post_date" value="p_specify" <?php if($post_date=="p_specify"){echo("checked");} ?>/><label for="specify">指定日</label><input type="date" name="specify_date" value="<?= $specify_date ?>"><br>

            <input type="radio" id="p_random" name="post_date" value="p_random"  <?php if($post_date=="p_random"){echo("checked");} ?>><label for="random">ランダムな過去日</label><input type="date" name="rand_start_date" value="<?= $rand_start_date ?>">～<input type="date" name="rand_end_date" value="<?= $rand_end_date ?>"><br>
        
            &nbsp;&nbsp;&nbsp;&nbsp;<input type="checkbox" name="limited_flag" value="1" <?php if($limited_flag){echo("checked");} ?>>投稿日は作品の「発売日」以降に限定する
        </td></tr>
        <tr><th>ランダムテキスト1<br>（※改行区切り）</th><td>
            <textarea style="width:100%;height:120px" name="random_text1"><?= $random_text1 ?></textarea>
        </td></tr>
        <tr><th>ランダムテキスト2<br>（※改行区切り）</th><td>
            <textarea style="width:100%;height:120px" name="random_text2"><?= $random_text2 ?></textarea>
        </td></tr>
        <tr><th>ランダムテキスト3<br>（※改行区切り）</th><td>
            <textarea style="width:100%;height:120px" name="random_text3"><?= $random_text3 ?></textarea>
        </td></tr>
        <tr><td colspan="2"></td></tr>
        <tr><th>投稿ステータス（post_status）</th><td>
            <select name="output" aria-describedby="outputHelpBlock">
                                <?php
                                    echo $this->make_option($this->post_status_ary, $output);
                                ?>
            </select>
        </td></tr>
        <tr><td colspan="2"></td></tr>
            <tr><th>DMM API ID<span style="color:red;">（*必須）</span></th><td>
            <input type="text" id="api_id" name="api_id" class="form-control" aria-describedby="api_idHelpBlock" value="<?= $api_id ?>" required />
            <!-- <input type="text" name="dmm_api_id" value="" /> -->
            &nbsp;*[<a href="https://affiliate.dmm.com/api/id_confirm/" target="_blank">DMMアフィリエイトのAPI ID</a>]を指定</td></tr>
            <tr><th>DMM アフィリエイトID<span style="color:red;">（*必須）</span></th><td>
            <!-- <input type="text" name="dmm_affi_id" value="" /> -->
            <input type="text" id="aff_id" name="aff_id" class="form-control" aria-describedby="aff_idHelpBlock" value="<?= $aff_id ?>" required />
            &nbsp;*[<a href="https://affiliate.dmm.com/account/index/" target="_blank">末尾990～999いずれかのアフィリエイトID</a>]を指定（例：xxxxx-990）</td></tr>
        </table>

        </div>

        <script>
        jQuery('#collapseSetting').click(function() {
            flag = jQuery('#collapseSetting').attr('aria-expanded');
            if(flag == "true"){
                jQuery('#collapse_triangle').html('▼')
            }else{
                jQuery('#collapse_triangle').html('▲')
            }
        })
        </script>


        <br>
        <table border="1" style="border: 15px solid black; border-collapse: collapse; color:white; background-color:black; width:99%;">
        <tr><td>投稿設定<?= $set_menu_number ?>：検索条件</td></tr>
        </table>

        <table class="setting" border="1" style="width:99%; border: 1px solid black; border-collapse: collapse;">
        <tr><th>検索キーワード<br> （※参考：<a href="https://support.dmm.com/others/article/12107" target="_blank">商品検索方法</a>）</th><td>
            <input type="text" id="keyword" name="keyword" class="form-control" aria-describedby="keywordHelpBlock" value="<?= $keyword ?>" size="25" />
        </td></tr>
        <tr><th>フロア</th><td>
        <select name="floor" class="form-select" aria-describedby="floorHelpBlock">
                    <?php
                        echo $this->make_floor_option($floor);
                    ?>
        </select>
        <input type="hidden" name="flr_name" value="" />
        </td></tr>

        <tr><th>絞り込み&nbsp;（<a href="https://stirring-opossum-ff6.notion.site/FANZA-Auto-plugin-113742bebf2880dfab15e8c35a068a0b" target="_blank">指定方法解説</a>）</th><td>
        <select name="article_type" class="form-select" aria-describedby="floorHelpBlock">
                    <?php
                        echo $this->make_option($this->article_ary, $article_type);
                    ?>
        </select>
        &nbsp;&nbsp;
        ID:<input type="text" name="article_id" value="<?= $article_id ?>" />
        </td></tr>

        <tr><th>検索(投稿)件数</th><td>
            <input type="number" id="hits" name="hits" aria-describedby="" placeholder="10" pattern="^[0-9]+$" min="1" max="100" value="<?= $hits ?>" />
        </td></tr>
        <tr><th>ソート順</th><td>
        <select name="sort" aria-describedby="sortHelpBlock">
                            <?php
                                echo $this->make_option($this->sort_ary, $sort);
                            ?>
        </select>
        </td></tr>
        <tr><th>発売日絞り込み</th><td>
            <input type="date" id="from_date" name="from_date" class="" aria-describedby="from_dateHelpBlock" value="<?= $from_date ?>" />
            ～
            <input type="date" id="to_date" name="to_date" class="" aria-describedby="to_dateHelpBlock" value="<?= $to_date ?>" />
        </td></tr>

        </table>

        <script>
        jQuery(function(){
            jQuery('[name=flr_name]').val(jQuery('[name=floor] option:selected').text());
        });
        jQuery('[name=floor]').change(function(){
            jQuery('[name=flr_name]').val(jQuery('[name=floor] option:selected').text());
        });
        </script>

        <!-- ================================ -->

            <br>
                
                <div class="col-12">

                    <input type="hidden" name="set_menu_number" value="<?= $set_menu_number ?>" />
                    <button type="submit" name="fanza_auto_save_submit" value="1" class="btn btn-primary" formaction="<?=  admin_url('admin.php') ?>?page=fanza-auto-menu<?= $set_menu_number ?>">設定保存</button>&nbsp;&nbsp;

                    <button type="submit" name="fanza_auto_search_submit" value="1" class="btn btn-primary" formaction="<?=  admin_url('admin.php') ?>?page=fanza-auto-menu<?= $set_menu_number ?>">設定保存＋検索</button>&nbsp;&nbsp;

                    <button type="submit" name="fanza_auto_quick_exe" value="1" class="btn btn-primary" formaction="<?=  admin_url('admin.php') ?>?page=fanza-auto-menu<?= $set_menu_number ?>" onclick="return confirm('即時投稿してよろしいですか？')">設定保存＋この検索条件で即時投稿</button>

                    <span id="span_status"><?php if(isset($this->search_submit)){echo("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[保存完了]");} ?></span>
                </div>
            </form>
            <?= $this->complete ?>
            <p style="text-align:right;"><a href="https://affiliate.dmm.com/api/" target="_blank"><img src="https://p.dmm.co.jp/p/affiliate/web_service/r18_135_17.gif" width="135" height="17" alt="WEB SERVICE BY FANZA" /></a></p>
        </div>

        <?php
    }


    /**
     * [1] First View
     */
    function show_config_form1() {
        $set_menu_number = "1";
        $this->post_set_page($set_menu_number);
    }
    function show_config_form2() {
        $set_menu_number = "2";
        $this->post_set_page($set_menu_number);
    }
    function show_config_form3() {
        $set_menu_number = "3";
        $this->post_set_page($set_menu_number);
    }
    function show_config_form4() {
        $set_menu_number = "4";
        $this->post_set_page($set_menu_number);
    }
    // ----------------------------------------------------------- //

    /**
     * mp4 process
     */
    function getSampleMovie2($list, $poster_url){
        // $this->dump("[list]");
        // $this->dump($list);

        $smovie_rich = "";
        $mp4_url = "";
        if (isset($list->sampleMovieURL)) {
            $data_movie_url = $list->sampleMovieURL->size_720_480;
            $mp4_url = $this->getMp4Url($data_movie_url);

            // $this->dump($mp4_url);

        }elseif(isset($list->sampleImageURL->sample_s)){
            $img = $list->sampleImageURL->sample_s->image[0];
            // $this->dump("[img]");
            // $this->dump($img);

            $short_img_ary = explode('/', $img);
            $short_img = end($short_img_ary);
            $short_cid = explode('-', $short_img)[0];

            // $this->dump($short_cid);
            $mp4_url = $this->getMp4FromCid($short_cid);
            // $this->dump($mp4_url);

            if($mp4_url == ""){
                $short_cid = substr($list->content_id, 0, -3);
                // $this->dump($short_cid);
                $mp4_url = $this->getMp4FromCid($short_cid);
                // $this->dump($mp4_url);
            }

            if($mp4_url == ""){
                $content_id = $list->content_id;
                // $this->dump($content_id);
                $mp4_url = $this->getMp4FromCid($content_id);
                // $this->dump($mp4_url);
            }

        }

        if($mp4_url){
            $smovie_rich .= '<!-- wp:html -->'."\n";
            $smovie_rich .= '<p style="text-align:center;">';
            $smovie_rich .= '<video src="'.$mp4_url.'" poster="';
            $smovie_rich .= $poster_url;
            $smovie_rich .= '" controls width="100%" height="100%" style="cursor:pointer; object-fit:cover;"></video>'."\n";
            $smovie_rich .= '</p>'."\n".'<!-- /wp:html -->'."\n";
        }

        return $smovie_rich;
    }

    function checkUrl($mp4_url){
        // var_dump($mp4_url);
        $context = stream_context_create([
            'http' => [
                'ignore_errors' => true
            ]
        ]);
        $res = file_get_contents($mp4_url, false, $context);
        // var_dump($res);

        if (strpos($http_response_header[0], '200') !== false) {
            // var_dump("200 ok");
            return true;
        } else {
            // var_dump("error");
            return false;
        }
    }

    function getMp4Url($data_movie_url) {
        $cid = mb_strstr($data_movie_url, "cid=");
        $cid = str_replace('cid=', '', $cid);
        $cid = mb_strstr($cid, "/", true);

        // $this->dump("[cid X]");
        // $this->dump($cid);

        $base_url = "https://cc3001.dmm.co.jp/litevideo/freepv/";
        // $middle_url = substr($cid, 0, 1);
        // if(check_url($mp4_url)){

        $middle_url = substr($cid, 0, 1)."/".substr($cid, 0, 3)."/".$cid."/".$cid;
        $mp4_url = $base_url . $middle_url . "mhb.mp4";
        if($this->checkUrl($mp4_url)) return $mp4_url;
        $mp4_url = $base_url . $middle_url . "dmb.mp4";
        if($this->checkUrl($mp4_url)) return $mp4_url;
        $mp4_url = $base_url . $middle_url . "dm.mp4";
        if($this->checkUrl($mp4_url)) return $mp4_url;
        $mp4_url = $base_url . $middle_url . "sm.mp4";
        if($this->checkUrl($mp4_url)) return $mp4_url;
        return "";
    }

    function getMp4FromCid($cid) {
        $base_url = "https://cc3001.dmm.co.jp/litevideo/freepv/";
        // $middle_url = substr($cid, 0, 1);
        // if(check_url($mp4_url)){

        $middle_url = substr($cid, 0, 1)."/".substr($cid, 0, 3)."/".$cid."/".$cid;
        // $this->dump($middle_url);

        $mp4_url = $base_url . $middle_url . "_mhb_w.mp4";
        if($this->checkUrl($mp4_url)) return $mp4_url;
        $mp4_url = $base_url . $middle_url . "_mhb_s.mp4";
        if($this->checkUrl($mp4_url)) return $mp4_url;
        $mp4_url = $base_url . $middle_url . "_dmb_w.mp4";
        if($this->checkUrl($mp4_url)) return $mp4_url;
        $mp4_url = $base_url . $middle_url . "_dmb_s.mp4";
        if($this->checkUrl($mp4_url)) return $mp4_url;
        $mp4_url = $base_url . $middle_url . "_dm_w.mp4";
        if($this->checkUrl($mp4_url)) return $mp4_url;
        $mp4_url = $base_url . $middle_url . "_dm_s.mp4";
        if($this->checkUrl($mp4_url)) return $mp4_url;
        $mp4_url = $base_url . $middle_url . "_sm_w.mp4";
        if($this->checkUrl($mp4_url)) return $mp4_url;
        $mp4_url = $base_url . $middle_url . "_sm_s.mp4";
        if($this->checkUrl($mp4_url)) return $mp4_url;
        return "";
    }

    /**
     * HTML parts generate
     */
    function make_option($option_arry, $selected) {
        $option_cont = '';
        foreach($option_arry as $key => $value) {
            if ($selected == $key) {
                $option_cont .= "<option value=\"$key\" selected>$value</option>\n";
            } else {
                $option_cont .= "<option value=\"$key\">$value</option>\n";
            }
        }
        return $option_cont;
    }

    function make_floor_option($selected) {
        $option_cont = '';

        foreach($this->floor_array as $floor) {
            $key = $floor[1].'/'.$floor[3].'/'.$floor[5];
            $value = str_replace('（アダルト）','',$floor[0]).' - '.$floor[2].' - '.$floor[4];
            if($selected === $key) {
                $option_cont .= "<option value=\"$key\" selected>$value</option>\n";
            } else {
                $option_cont .= "<option value=\"$key\">$value</option>\n";
            }
        }
        return $option_cont;
    }

    function make_ex_check_box($terms, $check, $name) {
        $check_box_cont = '';
        foreach($terms as $term) {
            if (in_array($term->slug, $check)) {
                $check_box_cont .= "<input type=\"checkbox\" name=\"{$name}[]\" value=\"{$term->slug}\" checked><label>{$term->name}</label><br />\n";
            } else {
                $check_box_cont .= "<input type=\"checkbox\" name=\"{$name}[]\" value=\"{$term->slug}\"><label>{$term->name}</label><br />\n";
            }
        }
        return $check_box_cont;
    }

    function make_cate_check_box($option_arry, $category) {
        $check_box_cont = '';
        foreach($option_arry as $key => $value) {
            if (in_array($key, $category)) {
                $check_box_cont .= "<input type=\"checkbox\" name=\"cate[]\" value=\"$key\" id=\"cate_{$key}\" checked><label for=\"cate_{$key}\">$value</label>&nbsp;&nbsp;\n";
            } else {
                $check_box_cont .= "<input type=\"checkbox\" name=\"cate[]\" value=\"$key\" id=\"cate_{$key}\"><label for=\"cate_{$key}\">$value</label>&nbsp;&nbsp;\n";
            }
        }
        return $check_box_cont;
    }

    function make_tag_check_box($option_arry, $tags) {
        $check_box_cont = '';
        foreach($option_arry as $key => $value) {
            if (in_array($key, $tags)) {
                $check_box_cont .= "<input type=\"checkbox\" name=\"tag[]\" value=\"$key\" id=\"tag_{$key}\" checked><label for=\"tag_{$key}\">$value</label>&nbsp;&nbsp;\n";
            } else {
                $check_box_cont .= "<input type=\"checkbox\" name=\"tag[]\" value=\"$key\" id=\"tag_{$key}\"><label for=\"tag_{$key}\">$value</label>&nbsp;&nbsp;\n";
            }
        }
        return $check_box_cont;
    }

    function make_hour_check_box($option_arry, $hour_list, $select_list) {
        $check_box_cont = '';
        foreach($option_arry as $key => $value) {
            $hnum = str_replace('h0','',$key);
            $hnum = str_replace('h','',$hnum);
            $select_one = "1";
            if($select_list) $select_one = $select_list[$hnum];
            $select1 = "";
            $select2 = "";
            $select3 = "";
            $select4 = "";
            if($select_one == '1'){$select1 ='checked';}
            if($select_one == '2'){$select2 ='checked';}
            if($select_one == '3'){$select3 ='checked';}
            if($select_one == '4'){$select4 ='checked';}

            $hour_checked = "";
            if (in_array($key, $hour_list)) $hour_checked = "checked";

            $check_box_cont .= "<label class='checkboxgroup' for=\"hour_{$key}\"><input type=\"checkbox\" name=\"hour_list[]\" value=\"$key\" id=\"hour_{$key}\" $hour_checked >$value</label>&nbsp;&nbsp;\n";
            $check_box_cont .= "（投稿設定：";
            $check_box_cont .= "<label for=\"hnum_{$key}_1\"><input type=\"radio\" name=\"hour_number[{$key}][]\" value=\"1\" id=\"hnum_{$key}_1\" ".$select1.">1&nbsp;&nbsp;</label>\n";
            $check_box_cont .= "<label for=\"hnum_{$key}_2\"><input type=\"radio\" name=\"hour_number[{$key}][]\" value=\"2\" id=\"hnum_{$key}_2\" ".$select2.">2&nbsp;&nbsp;</label>\n";
            $check_box_cont .= "<label for=\"hnum_{$key}_3\"><input type=\"radio\" name=\"hour_number[{$key}][]\" value=\"3\" id=\"hnum_{$key}_3\" ".$select3.">3&nbsp;&nbsp;</label>\n";
            $check_box_cont .= "<label for=\"hnum_{$key}_4\"><input type=\"radio\" name=\"hour_number[{$key}][]\" value=\"4\" id=\"hnum_{$key}_4\" ".$select4.">4&nbsp;&nbsp;</label>\n";
            $check_box_cont .= "）";

            $check_box_cont .= "<br>";
        }
        return $check_box_cont;
    }

    /**
     * Auto Excecution
     */
    function quick_exe() {
        if(isset($_POST['fanza_auto_quick_exe'])){
            // var_dump("quick_exe_XXXXXX");

            $set_menu_number = $_POST['set_menu_number'];
            $template_number = "";
            if($set_menu_number != "1") $template_number = $set_menu_number;
    
            list($lists, $service, $floor, $duplicate_count, $total_count) = $this->serch_contents_process("manual", $set_menu_number);

            global $wpdb;
            // end if empty
            if (empty($lists)) {
                return;
            }
            
            // echo '<script>console.log("[aaa]");</script>';
            // echo '<script>console.log("'.count($lists).'");</script>';

            // テンプレートを取得
            $table_prefix = $wpdb->prefix;
            $query = "SELECT id, post_content FROM {$table_prefix}posts WHERE post_title ='FANZAテンプレート".$template_number."' && post_type='post' && post_status = 'draft' ORDER BY post_date desc limit 1";
            $template_id = '';
            $post_content = '';
            // Next if title is the same
            $result = $wpdb->get_results($query, OBJECT);
            foreach ($result as $row) {
                    $template_id = $row->id;
                    $post_content = $row->post_content;
            }            

            $this->complete .='<p>投稿完了</p>';
            $this->complete .='<hr>';
            foreach($lists as $list){
                $this->post_contents_process($list, $post_content, $wpdb, "", "", $set_menu_number);
            }

            $this->complete .='<hr>';
            $this->complete .='<p>投稿完了</p>';
            $this->contents_array = array();
        }
    }

    function textareaEscape($text){
        $text = str_replace(array("\r\n", "\r", "\n"), "\n", $text);
        $text = preg_replace('/^\n/m', '', $text);
        $text = str_replace('\"', '"', $text);
        $text = str_replace("\'", "'", $text);
        $text = str_replace("\\\\", "\\", $text);
        $text = trim($text);
        return $text;
    }

    function save_config_process(){

        $set_menu_number = $_POST['set_menu_number'];
        $number = "";
        if($set_menu_number != "1") $number = $set_menu_number.'_';


        ini_set('max_execution_time',900);
        ini_set('memory_limit', '512M');

        // get input items
        $maximage   = '';
        $hits       = '';
        $b_word     = '';
        $b_word2    = '';
        $api_id     = $_POST['api_id'];
        $aff_id     = $_POST['aff_id'];
        $eye        = $_POST['eye'];
        $poster     = $_POST['poster'];
        $floor      = "";
        if(isset($_POST['floor'])) $floor      = $_POST['floor'];
        $flr_name   = "";
        if(isset($_POST['flr_name'])) $flr_name = $_POST['flr_name'];
        $maximage   = $_POST['maximage'];
        $cate_other = '';
        if(isset($_POST['cate_other'])) $cate_other = $_POST['cate_other'];
        $cate_free  = $_POST['cate_free'];
        $tag_other = '';
        if(isset($_POST['tag_other'])) $tag_other = $_POST['tag_other'];
        $tag_free   = $_POST['tag_free'];
        $hits       = $_POST['hits'];
        $from_date  = $_POST['from_date'];
        $to_date    = $_POST['to_date'];
        $keyword    = $_POST['keyword'];
        $article_type = "";
        if(isset($_POST['article_type'])) $article_type = $_POST['article_type'];
        $article_id   = "";
        if(isset($_POST['article_id'])) $article_id   = $_POST['article_id'];
        $b_word     = $_POST['b_word'];
        $b_word2    = $_POST['b_word2'];
        $t_title    = '';
        if(isset($_POST['t_title'])) $t_title    = $_POST['t_title'];
        $t_excerpt  = '';
        if(isset($_POST['t_excerpt'])) $t_excerpt  = $_POST['t_excerpt'];
        $sort       = $_POST['sort'];
        $output     = $_POST['output'];
        $cate       = "";
        if(isset($_POST['cate'])) $cate = $_POST['cate'];
        $tag        = "";
        if(isset($_POST['tag'])) $tag = $_POST['tag'];
        $ex_cate    = "";
        if(isset($_POST['ex_cate'])) $ex_cate = $_POST['ex_cate'];
        $ex_tag     = "";
        if(isset($_POST['ex_tag'])) $ex_tag = $_POST['ex_tag'];
        $b_color    = $_POST['b_color'];
        $t_color    = $_POST['t_color'];
        $b_color2   = $_POST['b_color2'];
        $t_color2   = $_POST['t_color2'];
        $movie_size = $_POST['movie_size'];
        $post_date  = "";
        if(isset($_POST['post_date'])) $post_date = $_POST['post_date'];
        $specify_date    = $_POST['specify_date'];
        $rand_start_date = "";
        if(isset($_POST['rand_start_date'])) $rand_start_date = $_POST['rand_start_date'];
        $rand_end_date   = "";
        if(isset($_POST['rand_end_date'])) $rand_end_date = $_POST['rand_end_date'];
        $limited_flag    = "";
        if(isset($_POST['limited_flag'])) $limited_flag = $_POST['limited_flag'];
        $random_text1 = $_POST['random_text1'];
        $random_text2 = $_POST['random_text2'];
        $random_text3 = $_POST['random_text3'];

        if($from_date && $to_date){
            if($from_date > $to_date){
                $temp_date = $from_date;
                $from_date = $to_date;
                $to_date = $temp_date;
            }
        }
        if($rand_start_date && $rand_end_date){
            if($rand_start_date > $rand_end_date){
                $temp_date = $rand_start_date;
                $rand_start_date = $rand_end_date;
                $rand_end_date = $temp_date;
            }
        }

        if($hits === '') {
            $hits = 10;
        }
        if($b_word === '') {
            $b_word = 'この作品の価格を確認';
        }
        if($b_word2 === '') {
            $b_word2 = '続きの画像はこちら';
        }
        if($b_color == '') {
            $b_color = '#ff0000';
        }
        if($t_color == '') {
            $t_color = '#ffffff';
        }
        if($b_color2 == '') {
            $b_color2 = '#0000ff';
        }
        if($t_color2 == '') {
            $t_color2 = '#ffffff';
        }
        if($post_date === '') {
            $post_date = 'p_today';
        }
        $category = '';
        if(is_array($cate)) {
            $category = implode('/', $cate);
        } else {
            $category = $cate;
        }

        $tags = '';
        if(is_array($tag)) {
            $tags = implode('/', $tag);
        } else {
            $tags = $tag;
        }

        $ex_category = '';
        if(is_array($ex_cate)) {
            $ex_category = implode('/', $ex_cate);
        } else {
            $ex_category = $ex_cate;
        }

        $ex_tags = '';
        if(is_array($ex_tag)) {
            $ex_tags = implode('/', $ex_tag);
        } else {
            $ex_tags = $ex_tag;
        }
        
        // API IDID、アフィリエイトIDから半角スペース等を削除
        $api_id = str_replace(' ', '', $api_id);
        $api_id = str_replace('　', '', $api_id);
        $aff_id = str_replace(' ', '', $aff_id);
        $aff_id = str_replace('　', '', $aff_id);

        // アフィリエイトIDの下3桁をチェック
        $aff_no = substr($aff_id, -3);
        if (990 > $aff_no || $aff_no > 999) {
            $this->complete .= "<p style=\"color:red;\">アフィリエイトIDの下3桁を990から999で設定してください。</p>";
        }

        // save process
        update_option(self::DB_PREFIX . 'api_id', $api_id);
        update_option(self::DB_PREFIX . 'aff_id', $aff_id);

        update_option(self::DB_PREFIX . $number . 'eye', $eye);
        update_option(self::DB_PREFIX . $number . 'poster', $poster);
        update_option(self::DB_PREFIX . $number . 'floor', $floor);
        update_option(self::DB_PREFIX . $number . 'flr_name', $flr_name);
        update_option(self::DB_PREFIX . $number . 'maximage', $maximage);
        update_option(self::DB_PREFIX . $number . 'cate_other', $cate_other);
        update_option(self::DB_PREFIX . $number . 'cate_free', $cate_free);
        update_option(self::DB_PREFIX . $number . 'tag_other', $tag_other);
        update_option(self::DB_PREFIX . $number . 'tag_free', $tag_free);
        update_option(self::DB_PREFIX . $number . 'hits', $hits);
        update_option(self::DB_PREFIX . $number . 'from_date', $from_date);
        update_option(self::DB_PREFIX . $number . 'to_date', $to_date);
        update_option(self::DB_PREFIX . $number . 'keyword', $keyword);
        update_option(self::DB_PREFIX . $number . 'article_type', $article_type);
        update_option(self::DB_PREFIX . $number . 'article_id', $article_id);
        update_option(self::DB_PREFIX . $number . 'b_word', $b_word);
        update_option(self::DB_PREFIX . $number . 'b_word2', $b_word2);
        update_option(self::DB_PREFIX . $number . 't_title', $t_title);
        update_option(self::DB_PREFIX . $number . 't_excerpt', $t_excerpt);
        update_option(self::DB_PREFIX . $number . 'sort', $sort);
        update_option(self::DB_PREFIX . $number . 'output', $output);
        update_option(self::DB_PREFIX . $number . 'cate', $category);
        update_option(self::DB_PREFIX . $number . 'tag', $tags);
        update_option(self::DB_PREFIX . $number . 'ex_cate', $ex_category);
        update_option(self::DB_PREFIX . $number . 'ex_tag', $ex_tags);
        update_option(self::DB_PREFIX . $number . 'b_color', $b_color);
        update_option(self::DB_PREFIX . $number . 't_color', $t_color);
        update_option(self::DB_PREFIX . $number . 'b_color2', $b_color2);
        update_option(self::DB_PREFIX . $number . 't_color2', $t_color2);
        update_option(self::DB_PREFIX . $number . 'movie_size', $movie_size);
        update_option(self::DB_PREFIX . $number . 'post_date', $post_date);
        update_option(self::DB_PREFIX . $number . 'specify_date', $specify_date);
        update_option(self::DB_PREFIX . $number . 'rand_start_date', $rand_start_date);
        update_option(self::DB_PREFIX . $number . 'rand_end_date', $rand_end_date);
        update_option(self::DB_PREFIX . $number . 'limited_flag', $limited_flag);
        update_option(self::DB_PREFIX . $number . 'random_text1', $this->textareaEscape($random_text1));
        update_option(self::DB_PREFIX . $number . 'random_text2', $this->textareaEscape($random_text2));
        update_option(self::DB_PREFIX . $number . 'random_text3', $this->textareaEscape($random_text3));
    }

    /**
     * save [1] page
     */
    function save_config() {
        if (isset($_POST[self::NONCE_FIELD]) && $_POST[self::NONCE_FIELD]) {
            if (check_admin_referer(self::NONCE_ACTION, self::NONCE_FIELD)) {
                if(isset($_POST['fanza_auto_save_submit']) || isset($_POST['fanza_auto_search_submit']) || isset($_POST['fanza_auto_quick_exe'])){

                    $this->save_config_process();
                    
                }
            }
        }
    }

    // process functon
    function serch_contents_process($type, $set_menu_number="1") {
        // $this->auto_process_log("set_menu_number:" . $set_menu_number);

        $api_id     = get_option(self::DB_PREFIX . 'api_id');
        $aff_id     = get_option(self::DB_PREFIX . 'aff_id');
        
        $number = "";
        if($set_menu_number != "1") $number = $set_menu_number.'_';

        $floor      = get_option(self::DB_PREFIX . $number . 'floor');
        $hits       = get_option(self::DB_PREFIX . $number . 'hits');
        $from_date  = get_option(self::DB_PREFIX . $number . 'from_date');
        $to_date    = get_option(self::DB_PREFIX . $number . 'to_date');
        $keyword    = get_option(self::DB_PREFIX . $number . 'keyword');
        $article_type = get_option(self::DB_PREFIX . $number . 'article_type');
        $article_id   = get_option(self::DB_PREFIX . $number . 'article_id');
        $sort       = get_option(self::DB_PREFIX . $number . 'sort');

        if($hits == '') return ["","","","",""];

        // FANZA setting
        $fanza_set = explode('/', $floor);
        $site = $fanza_set[0];
        $service = $fanza_set[1];
        $floor = $fanza_set[2];

        $to = '';
        $from = '';
        // date setting
        if ($to_date != '') {
            $to = $to_date.'T23:59:59';
        }

        if ($from_date != '') {
            $from = $from_date.'T00:00:00';
        }

        // --------------------------------------- //
        // まず当日分（～3日前）を取り切る
        $lists_recent = [];

        if($type=="auto"){
            // $this->auto_process_log("hits:" . $hits . " count:" . count($lists_recent). " ====");

            $offset = 1;
            $s_date     = get_option(self::DB_PREFIX . 's_date');
            $e_date     = get_option(self::DB_PREFIX . 'e_date');
            $today      = get_option(self::DB_PREFIX . 'today');
            $threeday   = get_option(self::DB_PREFIX . 'threeday');
            $range      = get_option(self::DB_PREFIX . 'range');

            if($today || $threeday){
                if($today && $threeday){
                    $start_date = date_i18n("Y-m-d", strtotime('-3 day', current_time('timestamp'))).'T00:00:00';
                    $end_date = date_i18n("Y-m-d").'T23:59:59';
                }elseif($today){
                    $start_date = date_i18n("Y-m-d").'T00:00:00';
                    $end_date = date_i18n("Y-m-d").'T23:59:59';
                }else{
                    $start_date = date_i18n("Y-m-d", strtotime('-3 day', current_time('timestamp'))).'T00:00:00';
                    $end_date = date_i18n("Y-m-d", strtotime('-1 day', current_time('timestamp'))).'T23:59:59';

                }
                $kwd = urlencode($keyword);
                $url = "https://api.dmm.com/affiliate/v3/ItemList?api_id={$api_id}&affiliate_id={$aff_id}&site={$site}&service={$service}&floor={$floor}&keyword={$kwd}&sort={$sort}&output=json";
                if(($article_type != '') && ($article_id != '')){
                    $url .= "&article={$article_type}&article_id={$article_id}";
                }
                if ($start_date != '') {
                    $url .= "&gte_date={$start_date}";
                }
                if ($end_date != '') {
                    $url .= "&lte_date={$end_date}";
                }
                // echo($url);
                // var_dump("==url==1");
                // var_dump($url);

                // $this->auto_process_log("url 1: ".$url);

                list($lists_recent, $duplicate_count, $total_count) = $this->curl_get_list2($url, $offset, $hits, []);

                // $this->auto_process_log("hits:" . $hits . " count:" . count($lists_recent));

                if($lists_recent){
                    if(count($lists_recent) >= $hits){
                        return [$lists_recent, $service, $floor, $duplicate_count, $total_count];
                    }
                    if(!$range){
                        return [$lists_recent, $service, $floor, $duplicate_count, $total_count];
                    }
                    // $hits = $hits - count($lists_recent);

                }else{
                    if(!$range){
                        return ["","","","",""];
                    }
                }
            }

            // $this->auto_process_log("hits:" . $hits . "remain_hits:" . ($hits - count($lists_recent)) . " count:" . count($lists_recent) . " ----");

            if(!$range){
                return ["","","","",""];
            }

            $from = $s_date."T00:00:00";
            $to = $e_date."T23:59:59";

            // var_dump("==from==");
            // var_dump($from);
            // var_dump("==to==");
            // var_dump($to);
        
        }

        // --------------------------------------- //
        // 次に通常処理

        // request URL (for Search)
        $kwd = urlencode($keyword);
        $url = "https://api.dmm.com/affiliate/v3/ItemList?api_id={$api_id}&affiliate_id={$aff_id}&site={$site}&service={$service}&floor={$floor}&keyword={$kwd}&sort={$sort}&output=json";
        if(($article_type != '') && ($article_id != '')){
            $url .= "&article={$article_type}&article_id={$article_id}";
        }
        // $this->dump($url);

        if ($from != '') {
            if(!str_contains($from, 'T')) $from .= "T00:00:00";
            $url .= "&gte_date={$from}";
        }
        if ($to != '') {
            if(!str_contains($to, 'T')) $to .= "T23:59:59";
            $url .= "&lte_date={$to}";
        }
        // $url .= "&hits={$hits}";
        // $url .= "&offset={$offset}";
        // var_dump($url);

        // $lists = $this->curl_get_list($url);

        // $hits に到達するまで、繰り返しデータ取得する
        // $hits に余る分は除去して必要な分のみ返す

        // var_dump("==url==2");
        // var_dump($url);

        // $this->auto_process_log("url 2: ".$url);

        $lists = [];
        $offset = 1;
        list($lists, $duplicate_count, $total_count) = $this->curl_get_list2($url, $offset, $hits, $lists_recent);

        // if($type=="auto"){

        //     $lists = array_merge($lists_recent, $lists);

        //     return [$lists, $service, $floor, $duplicate_count, $total_count];
        // }
   
        // $this->dump($lists);

        return [$lists, $service, $floor, $duplicate_count, $total_count];
    }

    function getReview($list){
        // $performer = "";
        $review_count = '';
        $review_average = '';
        if(isset($list->review->count)) $review_count = $list->review->count;
        if(isset($list->review->average)){
            $review_average = $list->review->average;
        }else{
            $review_average = '-';
        }

        $review_img = "";
        if($review_average > 4.75){
            $review_img = 'https://p.dmm.co.jp/p/ms/review/5.gif';
        }elseif($review_average > 4.25){
            $review_img = 'https://p.dmm.co.jp/p/ms/review/4_5.gif';
        }elseif($review_average > 3.75){
            $review_img = 'https://p.dmm.co.jp/p/ms/review/4.gif';
        }elseif($review_average > 3.25){
            $review_img = 'https://p.dmm.co.jp/p/ms/review/3_5.gif';
        }elseif($review_average > 2.75){
            $review_img = 'https://p.dmm.co.jp/p/ms/review/3.gif';
        }elseif($review_average > 2.25){
            $review_img = 'https://p.dmm.co.jp/p/ms/review/2_5.gif';
        }elseif($review_average > 1.75){
            $review_img = 'https://p.dmm.co.jp/p/ms/review/2.gif';
        }elseif($review_average > 1.25){
            $review_img = 'https://p.dmm.co.jp/p/ms/review/1_5.gif';
        
        }elseif($review_average > 0.75){
            $review_img = 'https://p.dmm.co.jp/p/ms/review/1.gif';
        }else{
            $review_img = 'https://p.dmm.co.jp/p/ms/review/0.gif';
        }
        $review_html = "<img src='{$review_img}' />&nbsp;<span style='font-size: 80%;'>{$review_average}</span>";
        $review_html2 = $review_html;
        if($review_average == '-') $review_html2 = "";

        return [$review_html, $review_html2, $review_average, $review_count];
    }

    /**
     * Search content
     */
    function search_contents($set_menu_number) {

        list($lists, $service, $floor, $duplicate_count, $total_count) = $this->serch_contents_process("manual", $set_menu_number);
        $this->duplicate_count = $duplicate_count;
        $this->total_count = $total_count;

        global $wpdb;
        // end if empty
        if (empty($lists)) {
            return;
        }
        
        foreach ($lists as $list) {
            $duplicate = '';

            // $this->dump($list);
            
            $table_prefix = $wpdb->prefix;
            $query = "SELECT post_name FROM {$table_prefix}posts WHERE post_name ='{$list->content_id}'";
            $id='';
            // Next if title is the same
            $result = $wpdb->get_results($query, OBJECT);
            foreach ($result as $row) {
                    $id = $row->post_name;
            }
            if ($id == $list->content_id) {
                $duplicate = 'on';
                continue;
            }

            // Content ID
            $cid = $list->content_id;
            // Title
            $title = $list->title;
            // thumbnail
            if(isset($list->imageURL->large)) {
                $thumbnail = $list->imageURL->large;
            } else {
                $thumbnail = plugin_dir_url( __FILE__ )."/images/no-image.jpg";
            }

            $URL = $list->URL;
            $date = $list->date;
            $volume = "";
            if(isset($list->volume)) $volume = $list->volume;

            $actress_str = "";
            if(isset($list->iteminfo->actress)) {
                $actress = $list->iteminfo->actress;
                // echo("<pre>");
                // var_dump($actress);
                
                $actress_array = array_column($actress, 'name');
                // var_dump($actress_array);
                // echo("</pre>");
                $actress_str = "";
                foreach($actress_array as $id => $value) {
                    if($actress_str != '') $actress_str .= '　';
                    // var_dump($value);
                    $actress_str .= $value;
                }
            }

            $maker_str = "";
            if(isset($list->iteminfo->maker)) {
                $maker = $list->iteminfo->maker;
                $maker_array = array_column($maker, 'name');
                $maker_str ="";
                foreach($maker_array as $id => $value) {
                    if($maker_str != '') $maker_str .= '　';
                    $maker_str .= $value;
                }
            }

            $label_str = "";
            if(isset($list->iteminfo->label)) {
                $label = $list->iteminfo->label;
                $label_array = array_column($label, 'name');
                $label_str ="";
                foreach($label_array as $id => $value) {
                    if($label_str != '') $label_str .= '　';
                    $label_str .= $value;
                }
            }

            $director_str = "";
            if(isset($list->iteminfo->director)) {
                $director = $list->iteminfo->director;
                $director_array = array_column($director, 'name');
                $director_str ="";
                foreach($director_array as $id => $value) {
                    if($director_str != '') $director_str .= '　';
                    $director_str .= $value;
                }
            }

            $series_str = "";
            if(isset($list->iteminfo->series)) {
                $series = $list->iteminfo->series;
                $series_array = array_column($series, 'name');
                $series_str ="";
                foreach($series_array as $id => $value) {
                    if($series_str != '') $series_str .= '　';
                    $series_str .= $value;
                }
            }

            $author_str = "";
            if(isset($list->iteminfo->author)) {
                $author = $list->iteminfo->author;
                $author_array = array_column($author, 'name');
                $sauthor_str ="";
                foreach($author_array as $id => $value) {
                    if($author_str != '') $author_str .= '　';
                    $author_str .= $value;
                }
            }

            $genre_str = "";
            if(isset($list->iteminfo->genre)) {
                $genre = $list->iteminfo->genre;
                $genre_array = array_column($genre, 'name');
                $genre_str ="";
                foreach($genre_array as $id => $value) {
                    if($genre_str != '') $genre_str .= '　';
                    $genre_str .= $value;
                }
            }

            $manufacture = "";
            if(isset($list->iteminfo->manufacture)) {
                $manufacture = $list->iteminfo->manufacture[0]->name;
            }
            // $this->dump($manufacture);
            


            list($review_html, $review_html2, $review_average, $review_count) = $this->getReview($list);
            

            $this->contents_array[] = ['cid'=>$cid, 'duplicate'=>$duplicate,  'title'=>$title, 'thumbnail'=>$thumbnail, 'URL'=>$URL, 'date'=>$date, 'volume'=>$volume, 'actress'=>$actress_str, 'maker'=>$maker_str, 'label'=>$label_str,  'director'=>$director_str, 'series'=>$series_str, 'genre'=>$genre_str, 'review'=>$review_html, 'manufacture'=>$manufacture];
        }
    }

    // for be saved display
    function save_submit(){
        if (isset($_POST['fanza_auto_save_submit'])) {
            // echo("<script>jQuery(function(){ jQuery('#span_status').val('保存完了'); });</script>");
            $this->search_submit = '1';
        }
    }

    // Save auto exe settings
    function hour_submit(){
        if (isset($_POST['fanza_auto_hour_submit'])) {
            if (isset($_POST[self::NONCE_FIELD]) && $_POST[self::NONCE_FIELD]) {
                if (check_admin_referer(self::NONCE_ACTION, self::NONCE_FIELD)) {
    
                    $hour_number = "";
                    $hour_number = $_POST['hour_number'];
                    // echo("<pre>");
                    // var_dump($hour_number);
                    // echo("</pre>");
                    $exe_select = "";
                    if(is_array($hour_number)){        
                        foreach ($hour_number as $hnum){
                            if($exe_select) $exe_select .= '/';
                            $exe_select .= $hnum[0];
                            // echo("<pre>");
                            // var_dump($hnum[0]);
                            // echo("</pre>");
                        }
                    }
                    // var_dump($exe_select);

                    $hour_list = "";
                    if(isset($_POST['hour_list'])) $hour_list = $_POST['hour_list'];
                    $exe_hour = '';
                    if(is_array($hour_list)) {
                        $exe_hour = implode('/', $hour_list);
                    } else {
                        $exe_hour = $hour_list;
                    }
                    $today    = "";
                    $threeday = "";
                    $range    = "";
                    $auto_on    = "";
                    if(isset($_POST['today'])) $today = $_POST['today'];
                    if(isset($_POST['threeday'])) $threeday = $_POST['threeday'];
                    if(isset($_POST['range'])) $range = $_POST['range'];
                    if(isset($_POST['auto_on'])) $auto_on = $_POST['auto_on'];
                    $s_date   = $_POST['s_date'];
                    $e_date   = $_POST['e_date'];
                    $exe_min  = $_POST['exe_min'];
                    if(!$exe_min) $exe_min = $this->generate_unique_num(gethostname());


                    if($s_date > $e_date){
                        $temp_date = $s_date;
                        $s_date = $e_date;
                        $e_date = $temp_date;
                    }

                    update_option(self::DB_PREFIX . 'exe_hour', $exe_hour);
                    update_option(self::DB_PREFIX . 'today', $today);
                    update_option(self::DB_PREFIX . 'threeday', $threeday);
                    update_option(self::DB_PREFIX . 'range', $range);
                    update_option(self::DB_PREFIX . 's_date', $s_date);
                    update_option(self::DB_PREFIX . 'e_date', $e_date);
                    update_option(self::DB_PREFIX . 'exe_min', $exe_min);
                    update_option(self::DB_PREFIX . 'auto_on', $auto_on);
                    update_option(self::DB_PREFIX . 'exe_select', $exe_select);

                    $this->createAutoSchedule($auto_on);
                }
            }
        }
    }

    /**
     * for Disp search result
     */
    function printArray() {
        if (isset($_POST['fanza_auto_search_submit'])) {

            $set_menu_number = $_POST['set_menu_number'];

            $number = "";
            if($set_menu_number != "1") $number = $set_menu_number.'_';
            $this->search_contents($set_menu_number);

            $this->complete .= "<form method='POST' action='' name='post-form'>";
            wp_nonce_field(self::NONCE_ACTION, self::NONCE_FIELD);

            // $this->complete .='<p><input type="checkbox" name="all_check" id="all" checked>すべてチェック/解除</p>';
            // $this->complete .= "<table class='table'><thead><tr><th width='10%'>投稿</th><th width='30%'>タイトル</th><th width='10%'>パッケージ</th><th>追加コメント</th></thead>";

            $this->complete .= "検索結果：".count($this->contents_array)."件　（FANZA DB上の検索結果総数：".$this->total_count."件　　既に投稿済により除外：".$this->duplicate_count."件）";
            $this->complete .= "<table class='table'><thead><tr><th width='5%'>No・品番</th><th>タイトル・詳細</th><th width='20%'>パッケージ</th></thead>";
            $this->complete .= "<tbody>";
            $post_cnt = 0;
            $cid = '';

            $t_title = get_option(self::DB_PREFIX . $number . 't_title');

            for ($i=0; $i<count($this->contents_array); $i++) {
                $this->complete .= '<tr>';

                $this->complete .= '<td>';
                $this->complete .= '['.($i+1).']<br>';
                $this->complete .= $this->contents_array[$i]['cid'].'<br>';
                $this->complete .= '</td>';
                $this->complete .= '<td>';
                $this->complete .= '<a href="'.$this->contents_array[$i]['URL'].'" target="_blank">'.$this->contents_array[$i]['title'].'</a><br>';
                // $this->complete .= $this->contents_array[$i]['cid'].'<br>';

                $this->complete .= $this->contents_array[$i]['review'].'<br>';

                if(($this->contents_array[$i]['actress'] != '')){
                    $this->complete .= $this->contents_array[$i]['actress'].'<br>';
                }
                if(($this->contents_array[$i]['maker'] != '') || ($this->contents_array[$i]['label'] != '')){
                    if(($this->contents_array[$i]['maker'] != '')){
                        $this->complete .= $this->contents_array[$i]['maker'];
                        if(($this->contents_array[$i]['label'] != '')){
                            $this->complete .= '/';
                        }
                    }
                    if(($this->contents_array[$i]['label'] != '')){
                        $this->complete .= $this->contents_array[$i]['label'];
                    }
                    $this->complete .= '<br>';
                }
                if(($this->contents_array[$i]['manufacture']) != ''){
                    $this->complete .= $this->contents_array[$i]['manufacture'].'<br>';
                }
                if(($this->contents_array[$i]['volume']) != ''){
                    $this->complete .= $this->contents_array[$i]['volume'].'(分・枚)<br>';
                }
                $this->complete .= $this->contents_array[$i]['date'].'<br>';
                $this->complete .= '</td>';
                
                $this->complete .= '<td><img src="'.$this->contents_array[$i]['thumbnail'].'" width="200px" ></td>';
                $this->complete .= '</tr>';

            }
            $this->complete .= "</tbody></table>";
            $this->complete .= "</form>";
            $this->complete .= '<script src="https://code.jquery.com/jquery-3.4.1.min.js"></script>';
            $this->complete .= '<script>';
            $this->complete .= "$('#all').on('click',function() {";
            $this->complete .= "$('input[name=\"post_check[]\"]').prop('checked',this.checked);";
            $this->complete .= "});";
            $this->complete .= "$('input[name=\"post_check[]\"]').on('click',function(){";
            $this->complete .= "if($('.check :checked').length == $('.check input').length ) {";
            $this->complete .= "$('#all').prop('checked',true);";
            $this->complete .= "} else {";
            $this->complete .= "$('#all').prop('checked',false);";
            $this->complete .= "}";
            $this->complete .= "});";
            $this->complete .= "</script>";
        }
    }

    function rand_date_set($date, $rand_start_date, $rand_end_date, $limited_flag){
        if($rand_start_date && $rand_end_date){
            if($rand_start_date > $rand_end_date){
                $temp_date = $rand_start_date;
                $rand_start_date = $rand_end_date;
                $rand_end_date = $temp_date;
            }
        }

        $today = date_i18n('Y-m-d H:i:s', current_time('timestamp'));
        if($rand_end_date == ""){
            $end = $today;
        }else{
            $end = $rand_end_date.'T23:59:59';
            // $end = $rand_end_date.date_i18n(' H:i:s', current_time('timestamp'));
        } 

        if($limited_flag){
            if(str_contains($date, ' ')){
                $date = strstr($date, ' ', true);
            }
            $start = $date.'T00:00:00';
            // $start = $date.date_i18n(' H:i:s', current_time('timestamp'));
            if($rand_end_date < $date){
                $end = $today;
            }
        }else{
            $start = $rand_start_date.'T00:00:00';
            // $start = $rand_start_date.date_i18n(' H:i:s', current_time('timestamp'));
        }

        
        $min = strtotime($start);
        $max = strtotime($end);
        $date = rand($min, $max);
        $date = date_i18n('Y-m-d H:i:s', $date);

        return $date;
    }

    /**
     * 3つ目以降の画像をランダム取得（横長画像に限定）
     */
    function getImageAuto($large_image_arry){
        // var_dump("[[1]]");
        // var_dump(count($large_image_arry));
        if(count($large_image_arry) > 2){
            $image_arry = $large_image_arry;
            shuffle($image_arry);
            // $this->dump("[image_arry]");
            // $this->dump($image_arry);
            for($i=0; $i<count($image_arry); $i++) {
                if($image_arry[$i] == "") continue;
                list($width, $height) = getimagesize($image_arry[$i]);
                if($width > $height) {
                    return $image_arry[$i];
                    // break;
                }
            }
        }
    }

    // [2] Main process
    function post_contents_process($list, $post_content, $wpdb, $cont_title, $cont_comment, $set_menu_number="1"){

        // $this->auto_process_log("set_menu_number X :" . $set_menu_number);


        $dmm_id_is  = get_option(self::DB_PREFIX . 'dmm_id_is');
        if($dmm_id_is != 'OK') return;

        $api_id     = get_option(self::DB_PREFIX . 'api_id');
        $aff_id     = get_option(self::DB_PREFIX . 'aff_id');

        $number = "";
        if($set_menu_number != "1") $number = $set_menu_number.'_';

        // $this->auto_process_log("number:" . $number);


        $eye             = get_option(self::DB_PREFIX . $number . 'eye');
        $poster          = get_option(self::DB_PREFIX . $number . 'poster');
        $floor           = get_option(self::DB_PREFIX . $number . 'floor');
        $sort            = get_option(self::DB_PREFIX . $number . 'sort');
        $output          = get_option(self::DB_PREFIX . $number . 'output');
        $b_word          = get_option(self::DB_PREFIX . $number . 'b_word');
        $b_word2         = get_option(self::DB_PREFIX . $number . 'b_word2');
        $t_title         = get_option(self::DB_PREFIX . $number . 't_title');
        $t_excerpt       = get_option(self::DB_PREFIX . $number . 't_excerpt');
        $cate            = get_option(self::DB_PREFIX . $number . 'cate');
        $tag             = get_option(self::DB_PREFIX . $number . 'tag');
        $ex_cate         = get_option(self::DB_PREFIX . $number . 'ex_cate');
        $ex_tag          = get_option(self::DB_PREFIX . $number . 'ex_tag');
        $b_color         = get_option(self::DB_PREFIX . $number . 'b_color');
        $t_color         = get_option(self::DB_PREFIX . $number . 't_color');
        $b_color2        = get_option(self::DB_PREFIX . $number . 'b_color2');
        $t_color2        = get_option(self::DB_PREFIX . $number . 't_color2');
        $movie_size      = get_option(self::DB_PREFIX . $number . 'movie_size');
        $maximage        = get_option(self::DB_PREFIX . $number . 'maximage');
        $cate_other      = get_option(self::DB_PREFIX . $number . 'cate_other');
        $cate_free       = get_option(self::DB_PREFIX . $number . 'cate_free');
        $tag_other       = get_option(self::DB_PREFIX . $number . 'tag_other');
        $tag_free        = get_option(self::DB_PREFIX . $number . 'tag_free');
        $post_date       = get_option(self::DB_PREFIX . $number . 'post_date');
        $specify_date    = get_option(self::DB_PREFIX . $number . 'specify_date');
        $rand_start_date = get_option(self::DB_PREFIX . $number . 'rand_start_date');
        $rand_end_date   = get_option(self::DB_PREFIX . $number . 'rand_end_date');
        $limited_flag    = get_option(self::DB_PREFIX . $number . 'limited_flag');
        $random_text1    = get_option(self::DB_PREFIX . $number . 'random_text1');
        $random_text2    = get_option(self::DB_PREFIX . $number . 'random_text2');
        $random_text3    = get_option(self::DB_PREFIX . $number . 'random_text3');

        $category = explode('/', $cate);
        $tags = explode('/', $tag);
        $ex_category = explode('/', $ex_cate);
        $ex_tags = explode('/', $ex_tag);

        $random1 = "";
        if($random_text1){
            $random_text = str_replace(array("\r\n", "\r", "\n"), "\n", $random_text1);
            $random_ary = explode("\n", $random_text);
            $random1 = $random_ary[array_rand($random_ary, 1)];
        }
        $random2 = "";
        if($random_text2){
            $random_text = str_replace(array("\r\n", "\r", "\n"), "\n", $random_text2);
            $random_ary = explode("\n", $random_text);
            $random2 = $random_ary[array_rand($random_ary, 1)];
        }
        $random3 = "";
        if($random_text3){
            $random_text = str_replace(array("\r\n", "\r", "\n"), "\n", $random_text3);
            $random_ary = explode("\n", $random_text);
            $random3 = $random_ary[array_rand($random_ary, 1)];
        }

        // FANZA setting
        $fanza_set = explode('/', $floor);
        $site = $fanza_set[0];
        $service = $fanza_set[1];
        $floor = $fanza_set[2];

        // image directory
        $upload = wp_upload_dir(); 
        $IMG_DIR = $upload['path']  . '/';
        $IMG_URL = $upload['url'] . '/';


        $table_prefix = $wpdb->prefix;
        $query = "SELECT post_name FROM {$table_prefix}posts WHERE post_name ='$list->content_id'";
        $id='';
        // Next if title is the same
        $result = $wpdb->get_results($query, OBJECT);
        foreach ($result as $row) {
                $id = $row->post_name;
        }
        // 重複はスキップ
        if ($id == $list->content_id) {
            return;
        } 
        // URL
        $item_url = $list->URL;
        // Affiliate URL
        $affiliate = $list->affiliateURL;
        // Duration
        $volume = '';
        if(isset($list->volume)) $volume = $list->volume;
        
        list($review_html, $review_html2, $review_average, $review_count) = $this->getReview($list);
        
        // Title
        $title = $list->title;
        // Content ID
        $cid = $list->content_id;
        // Release Date
        if(isset($list->date)) {
            $onDate = mb_substr($list->date, 0, 10);
        } else {
            $onDate = '';
        }
        
        // jancode
        if (isset($list->jancode)) {
            $jancode = $list->jancode;
        }
        // maker_product
        if(isset($list->maker_product)) {
            $maker_product = $list->maker_product;
        }
        // cdinfo
        if(isset($list->cdinfo)) {
            $cdinfo = $list->cdinfo;
        }
        // isbn
        if(isset($list->isbn)) {
            $isbn = $list->isbn;
        }
        // stock
        if(isset($list->stock)) {
            $stock = $list->stock;
        }
        // prices
        if(isset($list->prices->list_price)) {
            $price = $list->prices->list_price;
        }
        
        $genres = array();
        $actor = array();
        $actress = array();
        $series = array();
        $maker = array();
        $director = array();
        $label = array();
        $author = array();
        $manufacture = array();

        $genres_array = array();
        $actor_array = array();
        $actress_array = array();
        $series_array = array();
        $maker_array = array();
        $director_array = array();
        $label_array = array();
        $author_array = array();
        $manufacture_array = array();

        // vartag用
        $actress_str = "";
        $performer = "";
        $maker_str = "";
        $label_str = "";
        $director_str = "";
        $series_str = "";
        $genre_str = "";
        $author_str = "";
        $manufacture_str = "";
        
        // Details
        // Genre
        if(isset($list->iteminfo->genre)) {
            $genres = $list->iteminfo->genre;
        }
        // Actor
        if(isset($list->iteminfo->actor)) {
            $actor = $list->iteminfo->actor;
        }  
        // Actress
        if(isset($list->iteminfo->actress)) {
            $actress = $list->iteminfo->actress;
        }
        // Series
        if(isset($list->iteminfo->series)) {
            $series = $list->iteminfo->series;
        }
        // Author
        if(isset($list->iteminfo->author)) {
            $author = $list->iteminfo->author;
        }
        // Maker
        if(isset($list->iteminfo->maker)) {
            $maker = $list->iteminfo->maker;
        }
        // Label
        if(isset($list->iteminfo->label)) {
            $label = $list->iteminfo->label;
        }
        // Director
        if(isset($list->iteminfo->director)) {
            $director = $list->iteminfo->director;
        }
        if(isset($list->iteminfo->manufacture)) {
            $manufacture = $list->iteminfo->manufacture;
        }

        // Content
        $content = '';
        $contentDoc = '';
        $comment_content = '';
        $comment_short = '';
        
        // post_content
        // Get scraping html
        // require_once(plugin_dir_path( __FILE__ ).'phpQuery-onefile.php'); 
        $curl = curl_init();
        $header = ['Referer: https://www.dmm.co.jp','Cookie: age_check_done=1'];
        $option = [
            CURLOPT_URL => $item_url,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_CONNECTTIMEOUT => 30,
            CURLOPT_HTTPHEADER     => $header,
        ];
        curl_setopt_array($curl, $option);
        $html = curl_exec($curl);
        curl_close($curl);

        // Scraping
        // [comment]がある、もしくは同人フロアで「[scraping_large_img_arry]」がある場合のみに限定する XXX
        $doScraping = False;
        if($post_content == "") $doScraping = True;
        if(str_contains($t_title, '[comment')) $doScraping = True;
        if(str_contains($t_excerpt, '[comment')) $doScraping = True;
        if(str_contains($post_content, '[comment')) $doScraping = True;
        if($service === 'mono' || $floor === 'digital_pcgame' || $service === 'ebook' || $service === 'doujin' || $service === 'monthly'){
            if(str_contains($post_content, '[sample-cap]'))$doScraping = True;
            if(str_contains($post_content, '[sample-photo]'))$doScraping = True;
            if(str_contains($post_content, '[sample-flex]'))$doScraping = True;
            if(str_contains($post_content, '[sample-nolink]'))$doScraping = True;
            if(str_contains($post_content, '[sample-no-cap-link]'))$doScraping = True;
        }
        if($service === 'digital' && $floor === 'videoc') $doScraping = True;

        $scraping_large_img_arry = [];
        $scraping_small_img_arry = [];
        $contentDoc = "";
        $comment_content = "";
        $comment_short = "";
        if($doScraping){
            // var_dump("[doScraping]");

            // $doc = \phpQuery::newDocument($html);

            if($service === 'mono') {
                // $contentDoc .= $doc['p.mg-b20']->text();
                $temp = explode('<p class="mg-b20">', $html)[1];
                $temp = explode('</p>', $temp)[0];
                $contentDoc .= $temp;

                // XXX
                $html2 = strstr($html, '<ul id="sample-image-block"');
                $html2 = strstr($html2, '</ul>', true);
                // echo("============================");
                // echo("<pre>");
                // var_dump($html2);
                // echo("</pre>");
                // echo("============================");

                $item_list = explode('" alt="', $html2);

                foreach($item_list as $item){
                    // echo("<pre>");
                    // var_dump($item);
                    // echo("</pre>");

                    if(str_contains($item, '<img src="')){
                        $item = explode('<img src="', $item)[1];
                    }
                    if(str_contains($item, 'data-lazy="')){
                        $item = explode('data-lazy="', $item)[1];
                    }
                    // var_dump("item: ".$item);

                    if(str_contains($item, $cid.'-') && str_contains($item, '.jpg')){
                        $scraping_small_img_arry[] = $item;
                        $scraping_large_img_arry[] = str_replace($cid.'-', $cid.'jp-', $item);
                    }
                    if(str_contains($item, 'js-') && str_contains($item, '.jpg')){
                        $scraping_small_img_arry[] = $item;
                        $scraping_large_img_arry[] = str_replace('js-', 'jp-', $item);
                    }
                }
                // echo("<pre>");
                // var_dump($scraping_small_img_arry);
                // var_dump($scraping_large_img_arry);
                // echo("</pre>");

            } elseif($floor === 'digital_pcgame') {
                // $contentDoc .= $doc['p.text-overflow']->text();
                $temp = explode('<p class="text-overflow">', $html)[1];
                $temp = explode('</p>', $temp)[0];
                $contentDoc .= $temp;

                // XXX
                $html2 = strstr($html, '<ul class="image-slider">');
                $html2 = strstr($html2, '</ul>', true);
                $item_list = explode('" alt=""', $html2);
                foreach($item_list as $item){
                    
                    $item = strstr($item, '<img src="');
                    $item = str_replace('<img src="', '', $item);
                    // var_dump($item);

                    $scraping_large_img_arry[] = $item;
                    $scraping_small_img_arry[] = str_replace('jp-0','js-0', $item);
                }
                array_shift($scraping_large_img_arry);
                array_shift($scraping_small_img_arry);
                array_pop($scraping_large_img_arry);
                array_pop($scraping_small_img_arry);


            } elseif($service === 'ebook') {
                $html2 = strstr($html, '"description":"');
                $html2 = str_replace('"description":"', '', $html2);
                $html2 = strstr($html2, '","', true);
                $contentDoc .= $html2;

                // if(str_contains($title, '（単話）')){
                    $html3 = explode('<meta property="og:title" content="', $html)[1];
                    $html3 = explode('" />', $html3)[0];
                    $title = $html3;
                // }

                if(str_contains($html, '","@id":"https:\/\/book.dmm.co.jp\/list\/?label=')){
                    $html4 = explode('","@id":"https:\/\/book.dmm.co.jp\/list\/?label=', $html)[0];
                    $tmp = explode('"@type":"Thing","name":"', $html4);
                    $label_name = end($tmp);
                    if (empty($label)) $label[] = (object) ['id' => '', 'name' => $label_name];
                }
            
            } elseif($service === 'doujin') {
                // $contentDoc .= $doc['.summary__txt']->text();
                $temp = explode('<p class="summary__txt">', $html)[1];
                $temp = explode('</p>', $temp)[0];
                $contentDoc .= $temp;

                // XXX
                $html2 = strstr($html, '"image": ["');
                $html2 = strstr($html2, '],', true);
                $item_list = explode(',"', $html2);
                foreach($item_list as $item){
                    $item = strstr($item, '"', true);
                    $scraping_large_img_arry[] = $item;
                    $scraping_small_img_arry[] = str_replace('jp-0','js-0', $item);
                }
                array_shift($scraping_large_img_arry);
                array_shift($scraping_small_img_arry);

                // var_dump($scraping_large_img_arry);
                // var_dump($scraping_small_img_arry);
                
            } elseif($service === 'monthly') {
                // $contentDoc .= $doc['p.tx-productComment']->text();
                $temp = explode('<p class="tx-productComment">', $html)[1];
                $temp = explode('</p>', $temp)[0];
                $contentDoc .= $temp;

                // XXX
                $html2 = strstr($html, '<div class="bx-sample-image">');
                $html2 = strstr($html2, '</div>', true);
                $item_list = explode('"></a>', $html2);
                foreach($item_list as $item){
                    
                    $item = strstr($item, 'src="');
                    $item = str_replace('src="', '', $item);
                    // var_dump($item);

                    $scraping_small_img_arry[] = $item;
                    $scraping_large_img_arry[] = str_replace($cid.'-', $cid.'jp-', $item);
                }
                array_shift($scraping_large_img_arry);
                array_shift($scraping_small_img_arry);
                array_pop($scraping_large_img_arry);
                array_pop($scraping_small_img_arry);


            } elseif($service === 'digital') {
                // $contentDoc .= $doc['meta[name=description]']->attr('content');
                $description = explode('<meta name="description" content="', $html)[1];
                $description = explode('"', $description)[0];
                $contentDoc .= $description;

                if($floor === 'videoc'){
                    if(str_contains($html,'名前：')){
                        $performer = mb_strstr($html, '>名前：</td>');
                        $performer = strstr($performer, '</tr>', true);
                        $performer = strstr($performer, '<td>');
                        $performer = strstr($performer, '</td>', true);
                        $performer = trim($performer);
                        $performer = str_replace('\r\n','',$performer);
                        $performer = str_replace('\r','',$performer);
                        $performer = str_replace('\n','',$performer);
                        $performer = str_replace('<td>','',$performer);
                    }
                }
            }
            //  else {
            //     $contentDoc .= $doc['.mg-b20:eq(2)']->text();
            // } 
            // if ( $contentDoc === '') {
            //     $contentDoc .= $doc['.tx-productComment']->text();
            // }
            // if ( $contentDoc === '') {
            //     $contentDoc .= $doc['.area-detail-read']->text();
            // }


            


            $contentDoc = explode('----------------------------------------------------------------------',$contentDoc)[0];
            $contentDoc = str_replace('【FANZA(ファンザ)】', '', $contentDoc);
            $contentDoc = htmlspecialchars_decode($contentDoc);

            // $this->dump("contentDoc1");
            // $this->dump($contentDoc);

            if(str_contains($contentDoc, 'href="')){
                $doc_ary = explode('href="', $contentDoc);
                foreach($doc_ary as &$doc_one){
                    // $this->dump("contentDoc1-3");

                    $doc_ex =  explode('"', $doc_one);
                    // $this->dump($doc_one);
                    if(!str_contains($doc_ex[0], 'https://al.dmm.co.jp/') && str_contains($doc_ex[0], '.dmm.co.jp/')){
                        $doc_ex[0] = "https://al.dmm.co.jp/?lurl=".urlencode($doc_ex[0])."&af_id=".$aff_id;
                    }
                    $doc_one = implode('"', $doc_ex);
                }
                unset($doc_one);

                $contentDoc = implode('href="', $doc_ary);
            }

            // $this->dump("contentDoc2");
            // $this->dump($contentDoc);

            $contentDoc_short = "";
            if ( $contentDoc !== '') {
                $comment_content = "<!-- wp:quote -->\n<blockquote class=\"wp-block-quote\"><p>".$contentDoc."</p><cite>FANZA</cite></blockquote>\n<!-- /wp:quote -->\n";

                $stripDoc = strip_tags($contentDoc);
                if(mb_strlen($stripDoc) > 200){
                    $contentDoc_short = mb_substr($stripDoc, 0, 200).'…';
                }else{
                    $contentDoc_short = $stripDoc;
                }
                $comment_short = "<!-- wp:quote -->\n<blockquote class=\"wp-block-quote\"><p>".$contentDoc_short."</p></blockquote>\n<!-- /wp:quote -->\n";

            }
        }


        // Package image
        $package_img = '';
        $image_large = '';
        if (isset($list->imageURL->large)) {
            $image_large = $list->imageURL->large;
            if(str_contains($image_large, 'jm.jpg')) $image_large = str_replace('jm.jpg','jp.jpg',$image_large);
            if(str_contains($image_large, 'js.jpg')) $image_large = str_replace('js.jpg','jp.jpg',$image_large);

            list($width, $height) = @getimagesize($image_large);
            $package_img = '<!-- wp:image {"align":"center","sizeSlug":"large","linkDestination":"custom"} -->'."\n".'<div class="wp-block-image"><figure class="aligncenter size-large"><a href="'.$affiliate.'" target="_blank"><img src="'.$image_large.'" alt="'.$title.'" width="'.$width.'" height="'.$height.'" /></a></figure></div>'."\n".'<!-- /wp:image -->';
        }

        // Detail
        $detail_content_ul = '';    // Detail Tag
        $detail_content_table = ''; // Detail Table

        $detail_content_ul .= '<!-- wp:list -->'."\n".'<ul>';
        $detail_content_table .= '<!-- wp:table -->'."\n".'<figure class="wp-block-table"><table><tbody>';
        if ($review_html2 != '') {
            $detail_content_ul .= '<li>レビュー : '.$review_html2.'</li>';
            $detail_content_table .= "<tr><th>レビュー</th><td>{$review_html2}</td></tr>";
        }
        if (isset($onDate)) {
            $detail_content_ul .= '<li>発売日 : '.$onDate.'</li>';
            $detail_content_table .= "<tr><th>発売日</th><td>{$onDate}</td></tr>";
        }
        if (!empty($volume)) {
            if($service === 'ebook') {
                $volume .= 'ページ';
            } elseif($service === 'doujin') {
                if(str_contains($volume,"動画") || str_contains($volume,"画像") || str_contains($volume,"+α") || str_contains($volume,"本") || str_contains($volume,"分")){
                    # none
                }else{
                    $volume .= 'ページ';
                }
            } else {
                if(!str_contains($volume, ':')){
                    $volume .= '分';
                }
            }
            $detail_content_ul .= '<li>収録 : '.$volume.'</li>';
            $detail_content_table .= "<tr><th>収録</th><td>{$volume}</td></tr>";
        }
        // Series
        if (!empty($series)) {
            $detail_content_ul .=$this->make_list('シリーズ', $series, $category, $tags, 'seri');
            $detail_content_table .=$this->make_table('シリーズ', $series, $category, $tags, 'seri');
            $series_array = array_column($series, 'name');
            $series_str =  implode(" ", $series_array);
        }
        // Author
        if (!empty($author)) {
            $detail_content_ul .=$this->make_list('作者', $author, $category, $tags, 'author');
            $detail_content_table .=$this->make_table('作者', $author, $category, $tags, 'author');
            $author_array = array_column($author, 'name');
            $author_str =  implode(" ", $author_array);
        }
        // Genres 
        if (!empty($genres)) {
            $detail_content_ul .=$this->make_list('ジャンル', $genres, $category, $tags, 'jan');
            $detail_content_table .=$this->make_table('ジャンル', $genres, $category, $tags, 'jan');
            $genres_array = array_column($genres, 'name');
            $genre_str =  implode(" ", $genres_array);
        }
        // Actor
        if (!empty($actor)) {
            if ($floor == 'cd') {
                $detail_content_ul .=$this->make_list('アーティスト', $actor, $category, $tags, 'act');
                $detail_content_table .=$this->make_table('アーティスト', $actor, $category, $tags, 'act');
                $actor_array = array_column($actor, 'name');
            } else {
                $detail_content_ul .=$this->make_list('出演者', $actor, $category, $tags, 'act');
                $detail_content_table .=$this->make_table('出演者', $actor, $category, $tags, 'act');
                $actor_array = array_column($actor, 'name');
            } 
        }
        // Actress
        if (!empty($actress)) {
            $detail_content_ul .=$this->make_list('女優', $actress, $category, $tags, 'act');
            $detail_content_table .=$this->make_table('女優', $actress, $category, $tags, 'act');
            $actress_array = array_column($actress, 'name');
            $actress_str =  implode(" ", $actress_array);
        }
        // Performer
        if (!empty($performer)) {
            $performer_array = [["id"=>"dummy","name"=>$performer]];
            $performer_obj = json_decode(json_encode($performer_array));
            $detail_content_ul .=$this->make_list('出演者', $performer_obj, $category, $tags, 'performer');
            $detail_content_table .=$this->make_table('出演者', $performer_obj, $category, $tags, 'performer');
        }
        // Director
        if (!empty($director)) {
            $detail_content_ul .=$this->make_list('監督', $director, $category, $tags, 'director');
            $detail_content_table .=$this->make_table('監督', $director, $category, $tags, 'director');
            $director_array = array_column($director, 'name');
            $director_str =  implode(" ", $director_array);
        }
        // Maker
        if (!empty($maker)) {
            $maker_title_name = 'メーカー';
            if($floor === 'digital_doujin') $maker_title_name = 'サークル';
            $detail_content_ul .=$this->make_list($maker_title_name, $maker, $category, $tags, "maker");
            $detail_content_table .=$this->make_table($maker_title_name, $maker, $category, $tags, "maker");
            $maker_array = array_column($maker, 'name');
            $maker_str =  implode(" ", $maker_array);
        }
        // Label
        if (!empty($label)) {
            $detail_content_ul .=$this->make_list('レーベル', $label, $category, $tags, "label");
            $detail_content_table .=$this->make_table('レーベル', $label, $category, $tags, "label");
            $label_array = array_column($label, 'name');
            $label_str =  implode(" ", $label_array);
        }
        if (!empty($manufacture)) {
            $detail_content_ul .=$this->make_list('出版社', $manufacture, $category, $tags, "manufacture");
            $detail_content_table .=$this->make_table('出版社', $manufacture, $category, $tags, "manufacture");
            $manufacture_array = array_column($manufacture, 'name');
            $manufacture_str =  implode(" ", $manufacture_array);
        }

        // CID
        if (isset($cid)) {
            $detail_content_ul .= '<li>品番 : '. $cid.'</li>';
            $detail_content_table .= "<tr><th>品番</th><td>{$cid}</td></tr>";
        }
        // Jan Code
        if (isset($jancode)) {
            $detail_content_ul .= '<li>JANコード : '. $jancode.'</li>';
            $detail_content_table .= "<tr><th>JANコード</th><td>{$jancode}</td></tr>";
        }
        // Maker Product
        if (isset($maker_product)) {
            $detail_content_ul .= '<li>メーカー品番 : '. $maker_product.'</li>';
            $detail_content_table .= "<tr><th>メーカー品番</th><td>{$maker_product}</td></tr>";
        }
        // ISBN
        if (isset($isbn)) {
            $detail_content_ul .= '<li>ISBN : '. $isbn.'</li>';
            $detail_content_table .= "<tr><th>ISBN</th><td>{$isbn}</td></tr>";
        }
        // Price
        if (isset($price)) {
            $detail_content_ul .= '<li>価格 : ￥'. $price.'</li>';
            $detail_content_table .= "<tr><th>価格</th><td>￥{$price}</td></tr>";
        }
        $detail_content_ul .= '</ul><!-- /wp:list -->'."\n";
        $detail_content_table .= "</tbody></table></figure>\n<!-- /wp:table -->\n";
        

        // 女優ページ作成
        $act_page = '';
        $act_table = '';
        if (!empty($actress)) {
            $act_id_array = array_column($actress, 'id');
            foreach($act_id_array as $act_id) {
                // request URL
                $url = "https://api.dmm.com/affiliate/v3/ActressSearch?api_id={$api_id}&affiliate_id={$aff_id}&actress_id={$act_id}&hits=1&offset=1&sort=id&output=json";
                $act_list = $this->curl_get_list($url);
                // act_page作成メソッド
                list($actress_list, $actress_table) = $this->make_act_html($act_list);
                if($act_list){
                    $act_page = $actress_list;
                    $act_table = $actress_table;
                }
            }
        }

        // Tachiyomi
        $tachiyomi_content = '';
        $tachiyomi_link = '';
        if (isset($list->tachiyomi)) {
            $tachiyomi_link = $list->tachiyomi->affiliateURL;
            $tachiyomi_content = "<!-- wp:html -->\n".
                                '<div class="wp-block-buttons is-content-justification-center tachiyomi"><div class="wp-block-button has-custom-width wp-block-button__width-100 btn-lg"><a class="wp-block-button__link" target="_blank" href="'.$tachiyomi_link.'" style="border-radius:5px; color:' . $t_color . '; background-color:' . $b_color .'" >立ち読みはこちら</a></div></div>'."\n".
                                "<!-- /wp:html -->\n";
        }
        
        // Button
        $button_content = "<!-- wp:html -->\n".
                          '<div class="wp-block-buttons is-content-justification-center content1"><div class="wp-block-button has-custom-width wp-block-button__width-100 btn-lg"><a class="wp-block-button__link" href="'.$affiliate.'" style="border-radius:5px; color:' . $t_color . '; background-color:' . $b_color .'" target="_blank" rel="noreferrer noopener">'.$b_word.'</a></div></div>'."\n".
                          "<!-- /wp:html -->\n";

        // Button2
        $button_content2 = "<!-- wp:html -->\n".
                          '<div class="wp-block-buttons is-content-justification-center content2"><div class="wp-block-button has-custom-width wp-block-button__width-100 btn-lg"><a class="wp-block-button__link" href="'.$affiliate.'" style="border-radius:5px; color:' . $t_color2 . '; background-color:' . $b_color2 .'" target="_blank" rel="noreferrer noopener">'.$b_word2.'</a></div></div>'."\n".
                          "<!-- /wp:html -->\n";

        // Sample Image
        $small_image_arry = array();
        $large_image_arry = array();
        $sample_img_content = '';
        $sample_img_content_no = '';
        $sample_img_content_small = '';
        $sample_img_non = '';
        $sample_no_cap_link = '';
        if(isset($list->sampleImageURL) || ($scraping_large_img_arry)) {

            if(isset($list->sampleImageURL->sample_s)) {
                $small_image_arry = $list->sampleImageURL->sample_s->image;
            }
            if(isset($list->sampleImageURL->sample_l)) {
                $large_image_arry = $list->sampleImageURL->sample_l->image;
            }
            if(isset($list->sampleImageURL->sample_s) && !isset($list->sampleImageURL->sample_l)) {
                // $this->dump("[not sample_l XXX1]");
                $large_image_arry = $list->sampleImageURL->sample_s->image;
                foreach($large_image_arry as &$img) {
                    if(str_contains($img, 'js-')){
                        $img = str_replace('js-', 'jp-', $img);
                        if(!$this->checkUrl($img)){
                            $large_image_arry = array();
                            break;
                        }
                    }elseif(str_contains($img, '-')){
                        // $this->dump("[not sample_l XXX-2]");
                        // $this->dump($img);
                        $img = str_replace('-', 'jp-', $img);
                        // $this->dump($img);
                        if(!$this->checkUrl($img)){
                            $large_image_arry = array();
                            break;
                        }
                    }
                }
                unset($img);
                // $this->dump($large_image_arry);
            }

            // $this->dump("small_image_arry");
            // $this->dump($small_image_arry);
            // $this->dump("large_image_arry");
            // $this->dump($large_image_arry);

            if(empty($small_image_arry) && empty($large_image_arry)){
                // var_dump(count($scraping_large_img_arry));
                if($scraping_large_img_arry){
                    $large_image_arry = $scraping_large_img_arry;
                    $small_image_arry = $scraping_small_img_arry;
                }
            }

            if (!empty($large_image_arry)) {
                $cnt = 1;
                foreach($large_image_arry as $img) {
                    // var_dump($img);
                    // if($img == "") continue;

                    list($width, $height) = getimagesize($img);
                    $sample_img_content .= '<!-- wp:image {"align":"center","className":"aligncenter"} -->'."\n".'<div class="wp-block-image aligncenter"><figure class="aligncenter"><a href="'.$img.'" target="_blank" rel="noreferrer noopener"><img src="'.$img.'" alt="'.$title. ' 画像' . $cnt .'" width="'.$width.'" height="'.$height.'" /></a><figcaption>'.$title. ' 画像' . $cnt .'</figcaption></figure></div>'."\n".'<!-- /wp:image -->'."\n";
                    $sample_img_content_no .= '<!-- wp:image {"align":"center","className":"aligncenter"} -->'."\n".'<div class="wp-block-image aligncenter"><figure class="aligncenter"><a href="'.$img.'" target="_blank" rel="noreferrer noopener"><img src="'.$img.'" alt="'.$title. ' 画像' . $cnt .'" width="'.$width.'" height="'.$height.'" /></a></figure></div>'."\n".'<!-- /wp:image -->'."\n";
                    $sample_img_non .= '<!-- wp:image {"align":"center","className":"aligncenter"} -->'."\n".'<div class="wp-block-image aligncenter"><figure class="aligncenter"><img src="'.$img.'" alt="'.$title. ' 画像' . $cnt .'" width="'.$width.'" height="'.$height.'" /><figcaption>'.$title. ' 画像' . $cnt .'</figcaption></figure></div>'."\n".'<!-- /wp:image -->'."\n";
                    $sample_no_cap_link .= '<!-- wp:image {"align":"center","className":"aligncenter"} -->'."\n".'<div class="wp-block-image aligncenter"><figure class="aligncenter"><img src="'.$img.'" alt="'.$title. ' 画像' . $cnt .'" width="'.$width.'" height="'.$height.'" /></figure></div>'."\n".'<!-- /wp:image -->'."\n";
                    if($cnt == $maximage) break;
                    $cnt++;
                }
                            
            } else {
                $cnt = 1;
                if ( $floor === 'digital_pcgame') {
                    foreach($small_image_arry as $img) {
                        $img = str_replace('js', 'jp', $img);
                        list($width, $height) = getimagesize($img);
                        $sample_img_content .= '<!-- wp:image {"align":"center","className":"aligncenter"} -->'."\n".'<div class="wp-block-image aligncenter"><figure class="aligncenter"><a href="'.$img.'" target="_blank" rel="noreferrer noopener"><img src="'.$img.'" alt="'.$title. ' 画像' . $cnt .'" width="'.$width.'" height="'.$height.'" /></a><figcaption>'.$title. ' 画像' . $cnt .'</figcaption></figure></div>'."\n".'<!-- /wp:image -->'."\n";
                        $sample_img_content_no .= '<!-- wp:image {"align":"center","className":"aligncenter"} -->'."\n".'<div class="wp-block-image aligncenter"><figure class="aligncenter"><a href="'.$img.'" target="_blank" rel="noreferrer noopener"><img src="'.$img.'" alt="'.$title. ' 画像' . $cnt .'" width="'.$width.'" height="'.$height.'" /></a></figure></div>'."\n".'<!-- /wp:image -->'."\n";
                        $sample_img_non .= '<!-- wp:image {"align":"center","className":"aligncenter"} -->'."\n".'<div class="wp-block-image aligncenter"><figure class="aligncenter"><img src="'.$img.'" alt="'.$title. ' 画像' . $cnt .'" width="'.$width.'" height="'.$height.'" /><figcaption>'.$title. ' 画像' . $cnt .'</figcaption></figure></div>'."\n".'<!-- /wp:image -->'."\n";
                        $sample_no_cap_link .= '<!-- wp:image {"align":"center","className":"aligncenter"} -->'."\n".'<div class="wp-block-image aligncenter"><figure class="aligncenter"><img src="'.$img.'" alt="'.$title. ' 画像' . $cnt .'" width="'.$width.'" height="'.$height.'" /></figure></div>'."\n".'<!-- /wp:image -->'."\n";
                        if($cnt == $maximage) break;
                        $cnt++;
                    }
                } else {
                    foreach($small_image_arry as $img) {
                        list($width, $height) = getimagesize($img);
                        $sample_img_content .= '<!-- wp:image {"align":"center","className":"aligncenter"} -->'."\n".'<div class="wp-block-image aligncenter"><figure class="aligncenter"><a href="'.$img.'" target="_blank" rel="noreferrer noopener"><img src="'.$img.'" alt="'.$title. ' 画像' . $cnt .'" width="'.$width.'" height="'.$height.'" /></a><figcaption>'.$title. ' 画像' . $cnt .'</figcaption></figure></div>'."\n".'<!-- /wp:image -->'."\n";
                        $sample_img_content_no .= '<!-- wp:image {"align":"center","className":"aligncenter"} -->'."\n".'<div class="wp-block-image aligncenter"><figure class="aligncenter"><a href="'.$img.'" target="_blank" rel="noreferrer noopener"><img src="'.$img.'" alt="'.$title. ' 画像' . $cnt .'" width="'.$width.'" height="'.$height.'" /></a></figure></div>'."\n".'<!-- /wp:image -->'."\n";
                        $sample_img_non .= '<!-- wp:image {"align":"center","className":"aligncenter"} -->'."\n".'<div class="wp-block-image aligncenter"><figure class="aligncenter"><img src="'.$img.'" alt="'.$title. ' 画像' . $cnt .'" width="'.$width.'" height="'.$height.'" /><figcaption>'.$title. ' 画像' . $cnt .'</figcaption></figure></div>'."\n".'<!-- /wp:image -->'."\n";
                        $sample_no_cap_link .= '<!-- wp:image {"align":"center","className":"aligncenter"} -->'."\n".'<div class="wp-block-image aligncenter"><figure class="aligncenter"><img src="'.$img.'" alt="'.$title. ' 画像' . $cnt .'" width="'.$width.'" height="'.$height.'" /></figure></div>'."\n".'<!-- /wp:image -->'."\n";
                        if($cnt == $maximage) break;
                        $cnt++;
                    }
                }

                // $this->dump("[SSS 1]");
                $cnt = 1;
                $sample_img_content_small = "<!-- wp:html -->\n";
                $sample_img_content_small .= "<div style=\"display: flex; flex-wrap:wrap; justify-content: start;\">\n";
                for ($i=0; $i<count($small_image_arry); $i++) {
                    list($width, $height) = getimagesize($small_image_arry[$i]);
                    $sample_img_content_small .= "<div style=\"padding: 5px; width: 110px;\">".'<img src="'.$small_image_arry[$i].'" alt="'.$title. ' 画像' . $cnt ."\" width=\"{$width}\" height=\"{$height}\"/></div>\n";
                    if($cnt == $maximage) break;
                    $cnt++;
                }
                $sample_img_content_small .= "</div>\n";
                $sample_img_content_small .= "<!-- /wp:html -->\n";
            }
            if (!empty($large_image_arry) && !empty($small_image_arry)) {
                $cnt = 1;
                $sample_img_content_small = "<!-- wp:html -->\n";
                $sample_img_content_small .= "<div style=\"display: flex; flex-wrap:wrap; justify-content: start;\">\n";
                for ($i=0; $i<count($large_image_arry); $i++) {
                    list($width, $height) = getimagesize($small_image_arry[$i]);
                    $sample_img_content_small .= "<div style=\"padding: 5px; width: 110px;\"><a href=\"".$large_image_arry[$i]."\" target=\"_blank\" rel=\"noreferrer noopener\">".'<img src="'.$small_image_arry[$i].'" alt="'.$title. ' 画像' . $cnt ."\" width=\"{$width}\" height=\"{$height}\"/></a></div>\n";
                    if($cnt == $maximage) break;
                    $cnt++;
                }
                $sample_img_content_small .= "</div>\n";
                $sample_img_content_small .= "<!-- /wp:html -->\n";
            }
        }

        // API Mark
        if($site === 'FANZA') {
            $api_content = '<!-- wp:paragraph -->'."\n".'<p style="text-align:right;"><a href="https://affiliate.dmm.com/api/"><img src="https://p.dmm.co.jp/p/affiliate/web_service/r18_135_17.gif" width="135" height="17" alt="WEB SERVICE BY FANZA" /></a></p>'."\n".'<!-- /wp:paragraph -->'."\n";
        } else {
            $api_content = '<!-- wp:paragraph -->'."\n".'<p style="text-align:right;"><a href="https://affiliate.dmm.com/api/"><img src="https://pics.dmm.com/af/web_service/com_135_17.gif" width="135" height="17" alt="WEB SERVICE BY DMM.com" /></a></p>'."\n".'<!-- /wp:paragraph -->'."\n";
        }

        $post_comment = '';
        if ($cont_comment != '') {
            if(preg_match("/<(\"[^\"]*\"|'[^']*'|[^'\">])*>/", $cont_comment)) {
                $post_comment = '<!-- wp:html -->'."\n". $cont_comment."\n".'<!-- /wp:html -->'."\n";
            } else {
                $post_comment = '<!-- wp:paragraph -->'."\n<p>". $cont_comment."</p>\n".'<!-- /wp:paragraph -->'."\n";
            }
        }

        // アイキャッチ設定
        $img_name = '';
        $imginfo = '';
        $url = '';
        $img = '';
        // サンプル画像の場合
        if($eye !== 'none') {
            if($eye === 'sample') {
                if(count($large_image_arry) > 2){
                    $url = $this->getImageAuto($large_image_arry);
                    // $this->dump("[url 00]");
                    // $this->dump($url);
                }
            }
            if($eye === '1'){
                if(isset($large_image_arry[0])) $url = $large_image_arry[0];
            }
            if($eye === '2'){
                if(isset($large_image_arry[1])) $url = $large_image_arry[1];
            }
            if($eye === '3'){
                if(isset($large_image_arry[2])) $url = $large_image_arry[2];
            }
            if($eye === '4'){
                if(isset($large_image_arry[3])) $url = $large_image_arry[3];
            }
            if($eye === '99'){
                if(end($large_image_arry)) $url = end($large_image_arry);
            }

            if(!$url) {
                $url = $image_large;
                // $this->dump("[url 01]");
                // $this->dump($url);

                // if(isset($list->imageURL->large)) {
                //     $url = $list->imageURL->large;
                // }
            }

            if ($url !== '') {
                // var_dump($url);
                $imginfo = pathinfo($url);
                $img_name = $imginfo['basename'];
                // $this->dump("[url]");
                // $this->dump($url);
                // $this->dump("[img_name]");
                // $this->dump($img_name);

                // Save image
                $ch = curl_init($url);
                $fp = fopen($IMG_DIR.$img_name, 'w');
                // var_dump($IMG_DIR.$img_name);
                
                curl_setopt($ch, CURLOPT_FILE, $fp);
                curl_setopt($ch, CURLOPT_HEADER, 0);
                
                curl_exec($ch);
                curl_close($ch);
                fclose($fp);
            }
        }

        // poster画像
        $poster_url = '';
        if($poster !== 'none') {
            if($poster === 'sample') {
                $poster_url = $this->getImageAuto($large_image_arry);
            }
            if($poster_url === '') {
                $poster_url = $image_large;
                // if(isset($list->imageURL->large)) {
                //     $poster_url = $list->imageURL->large;
                // }
            }
        }

        // Sample movie
        $smovie_content = '';
        if (isset($list->sampleMovieURL)) {
            // var_dump("sampleMovieURL1");
                $smovie_content = '<!-- wp:html -->'."\n".'<p style="text-align:center;">';
                if ($movie_size === '476') {
                    $smovie_content .= '<iframe width="476" height="306" src="https://www.dmm.co.jp/litevideo/-/part/=/affi_id='.$aff_id.'/cid='.$cid.'/size=476_306/" scrolling="no" frameborder="0" allowfullscreen></iframe>';
                } elseif ($movie_size === '560') {
                    $smovie_content .= '<iframe width="560" height="360" src="https://www.dmm.co.jp/litevideo/-/part/=/affi_id='.$aff_id.'/cid='.$cid.'/size=560_360/" scrolling="no" frameborder="0" allowfullscreen></iframe>';
                } elseif ($movie_size === '644') {
                    $smovie_content .= '<iframe width="644" height="414" src="https://www.dmm.co.jp/litevideo/-/part/=/affi_id='.$aff_id.'/cid='.$cid.'/size=644_414/" scrolling="no" frameborder="0" allowfullscreen></iframe>';
                } elseif ($movie_size === '600') {
                    $smovie_content .= '<iframe width="600" height="500" src="https://www.dmm.co.jp/litevideo/-/part/=/affi_id='.$aff_id.'/cid='.$cid.'/size=600_500/" scrolling="no" frameborder="0" allowfullscreen></iframe>';
                } elseif($movie_size === '720') {
                    $smovie_content .= '<iframe width="720" height="480" src="https://www.dmm.co.jp/litevideo/-/part/=/affi_id='.$aff_id.'/cid='.$cid.'/size=720_480/" scrolling="no" frameborder="0" allowfullscreen></iframe>';
                } else {
                    $smovie_content .= '<div style="width:100%; padding-top:75%; position:relative;"><iframe width="100%" height="100%" max-width="1280px" style="position: absolute; top: 0; left: 0;" src="https://www.dmm.co.jp/litevideo/-/part/=/affi_id='.$aff_id.'/cid='.$cid.'/size=1280_720/" scrolling="no" frameborder="0" allowfullscreen></iframe></div>';
                }
                $smovie_content .= '</p>'."\n".'<!-- /wp:html -->'."\n";
        }

        if($cont_title == ''){
            $t_title    = get_option(self::DB_PREFIX . $number . 't_title');
            if($t_title){
                $cont_title = str_replace('[title]', $title, $t_title);
                $cont_title = str_replace('[cid]', $cid, $cont_title);
                $cont_title = str_replace('[actress]', $actress_str, $cont_title);
                $cont_title = str_replace('[performer]', $performer, $cont_title);
                $cont_title = str_replace('[maker]', $maker_str, $cont_title);
                $cont_title = str_replace('[label]', $label_str, $cont_title);
                $cont_title = str_replace('[publisher]', $manufacture_str, $cont_title);
                $cont_title = str_replace('[director]', $director_str, $cont_title);
                $cont_title = str_replace('[series]', $series_str, $cont_title);
                $cont_title = str_replace('[author]', $author_str, $cont_title);
                $cont_title = str_replace('[volume]', $volume, $cont_title);
                $cont_title = str_replace('[date]', $onDate, $cont_title);
                $cont_title = str_replace('[genre]', $genre_str, $cont_title);
                $cont_title = str_replace('[random1]', $random1, $cont_title);
                $cont_title = str_replace('[random2]', $random2, $cont_title);
                $cont_title = str_replace('[random3]', $random3, $cont_title);
                $cont_title = str_replace('[review-count]', $review_count, $cont_title);
                $cont_title = str_replace('[review-average]', $review_average, $cont_title);
            }else{
                $cont_title = $title;
            }
        }

        // サンプル動画リンク
        $sample_movie_link = '';
        if (isset($list->sampleMovieURL)) {
            $sample_movie_link = '<!-- wp:html -->'."\n";
            $sample_movie_link .= '<p style="text-align:center"><a href="'.$list->sampleMovieURL->size_720_480.'" target="_blank" rel=" noreferrer noopener"><img src="'.$IMG_URL.$img_name.'" alt="'.$cont_title.'" /></a></p>'."\n";
            $sample_movie_link .= '<!-- /wp:html -->';
        }

        // テンプレートがある場合
        if ($post_content) {
            $post_content = str_replace('<!-- wp:shortcode -->', '', $post_content);
            $post_content = str_replace('<!-- /wp:shortcode -->', '', $post_content);
            $post_content = str_replace('[title]', $title, $post_content);
            $post_content = str_replace('[cid]', $cid, $post_content);
            $post_content = str_replace('[aff-link]', $affiliate, $post_content);
            $post_content = str_replace('[detail-list]', $detail_content_ul, $post_content);
            $post_content = str_replace('[detail-table]', $detail_content_table, $post_content);
            $post_content = str_replace('[package]', $package_img, $post_content);
            if(str_contains($post_content, '[sample-movie2]')){
                $sample_movie2 = $this->getSampleMovie2($list, $poster_url);
                $post_content = str_replace('[sample-movie2]', $sample_movie2, $post_content);
            }
            $post_content = str_replace('[sample-movie]', $smovie_content, $post_content);
            $post_content = str_replace('[sample-movie-link]', $sample_movie_link, $post_content);
            $post_content = str_replace('[tachiyomi]', $tachiyomi_content, $post_content);
            $post_content = str_replace('[tachiyomi-link]', $tachiyomi_link, $post_content);
            // $post_content = str_replace('[sample-cap]', $sample_img_content, $post_content);
            // $post_content = str_replace('[sample-photo]', $sample_img_content_no, $post_content);
            $post_content = str_replace('[sample-cap]', $sample_img_non, $post_content);
            $post_content = str_replace('[sample-photo]', $sample_no_cap_link, $post_content);
            $post_content = str_replace('[sample-flex]', $sample_img_content_small, $post_content);
            $post_content = str_replace('[sample-nolink]', $sample_img_non, $post_content);
            $post_content = str_replace('[sample-no-cap-link]', $sample_no_cap_link, $post_content);
            $post_content = str_replace('[act-info]', $act_page, $post_content);
            $post_content = str_replace('[act-table]', $act_table, $post_content);
            $post_content = str_replace('[comment]', $comment_content, $post_content);
            $post_content = str_replace('[comment-short]', $comment_short, $post_content);
            $post_content = str_replace('[user-comment]', $post_comment, $post_content);
            $post_content = str_replace('[aff-button]', $button_content, $post_content);
            $post_content = str_replace('[aff-button2]', $button_content2, $post_content);

            $post_content = str_replace('[actress]', $actress_str, $post_content);
            $post_content = str_replace('[performer]', $performer, $post_content);
            $post_content = str_replace('[maker]', $maker_str, $post_content);
            $post_content = str_replace('[label]', $label_str, $post_content);
            $post_content = str_replace('[publisher]', $manufacture_str, $post_content);
            $post_content = str_replace('[director]', $director_str, $post_content);
            $post_content = str_replace('[series]', $series_str, $post_content);
            $post_content = str_replace('[author]', $author_str, $post_content);
            $post_content = str_replace('[volume]', $volume, $post_content);
            $post_content = str_replace('[date]', $onDate, $post_content);
            $post_content = str_replace('[genre]', $genre_str, $post_content);
            $post_content = str_replace('[random1]', $random1, $post_content);
            $post_content = str_replace('[random2]', $random2, $post_content);
            $post_content = str_replace('[random3]', $random3, $post_content);

            $post_content = str_replace('[review-count]', $review_count, $post_content);
            $post_content = str_replace('[review-average]', $review_average, $post_content);
            $post_content = str_replace('[review]', $review_html, $post_content);
            $post_content = str_replace('[review2]', $review_html2, $post_content);
            
            // LLM変数タグの処理
            $post_content = $this->process_llm_vartags($post_content, $list, $contentDoc);

            $content = $post_content;
            $content .= $api_content;
        // テンプレートがない場合
        } else {
            $content = $package_img;
            // $content .= $post_comment . $smovie_content . $tachiyomi_content . $button_content;
            $content .= $this->getSampleMovie2($list, $poster_url) . $tachiyomi_content . $button_content;
            if($sample_no_cap_link) {
                $content .= $sample_no_cap_link . $button_content;
            }
            $content .= $detail_content_table;
            $content .= $comment_content;
            $content .= $button_content;
            $content .= $api_content;
        }

        $post = array();
        // post_id
        $post['post_id'] = '';
        // post_type
        $post['post_type'] = 'post';
        // post_author
        $post['post_author'] = 1;

        // post_date
        $post['post_date'] = date_i18n('Y-m-d H:i:s', current_time('timestamp'));

        if($post_date == 'p_specify' && $specify_date){
            $post['post_date'] = $specify_date.date_i18n(' H:i:s', current_time('timestamp'));
        }

        if($post_date == 'p_random' && $rand_start_date){
            $post['post_date'] = $this->rand_date_set($onDate, $rand_start_date, $rand_end_date, $limited_flag);
        }


        // $this->auto_process_log("output:" . $output);



        // post_status
        $post['post_status'] = $output;
        // post_name
        $post['post_name'] = $cid;
        // post_title
        $post['post_title'] = $cont_title;
        // post_content
        $post['post_content'] = $content;
        // post_excerpt XXX
        if($t_excerpt){
            $excerpt = $t_excerpt;
            $excerpt = str_replace('[title]', $title, $excerpt);
            $excerpt = str_replace('[cid]', $cid, $excerpt);
            $excerpt = str_replace('[comment]', strip_tags($contentDoc), $excerpt);
            $excerpt = str_replace('[comment-short]', strip_tags($contentDoc_short), $excerpt);
            $excerpt = str_replace('[actress]', $actress_str, $excerpt);
            $excerpt = str_replace('[performer]', $performer, $excerpt);
            $excerpt = str_replace('[maker]', $maker_str, $excerpt);
            $excerpt = str_replace('[label]', $label_str, $excerpt);
            $excerpt = str_replace('[publisher]', $manufacture_str, $excerpt);
            $excerpt = str_replace('[director]', $director_str, $excerpt);
            $excerpt = str_replace('[series]', $series_str, $excerpt);
            $excerpt = str_replace('[author]', $author_str, $excerpt);
            $excerpt = str_replace('[volume]', $volume, $excerpt);
            $excerpt = str_replace('[date]', $onDate, $excerpt);
            $excerpt = str_replace('[genre]', $genre_str, $excerpt);
            $excerpt = str_replace('[random1]', $random1, $excerpt);
            $excerpt = str_replace('[random2]', $random2, $excerpt);
            $excerpt = str_replace('[random3]', $random3, $excerpt);
            $excerpt = str_replace('[review-count]', $review_count, $excerpt);
            $excerpt = str_replace('[review-average]', $review_average, $excerpt);

            $post['post_excerpt'] = $excerpt;

            // if ($contentDoc != '') {
            //     $post_excerpt = strip_tags($contentDoc);
            //     $post['post_excerpt'] = $post_excerpt;
            // }
        }
        
        // post_category
        $cate_list = array();
        if (in_array('jan', $category)) {
            $cate_list = array_merge($cate_list, $genres_array);
        }
        if (in_array('act', $category)) {
            $cate_list = array_merge($cate_list, $actress_array);
            $cate_list = array_merge($cate_list, $actor_array);
        }
        if (in_array('seri', $category)) {
            $cate_list = array_merge($cate_list, $series_array);
        }
        if (in_array('author', $category)) {
            $cate_list = array_merge($cate_list, $author_array);
        }
        if (in_array('maker', $category)) {
            $cate_list = array_merge($cate_list, $maker_array);
        }
        if (in_array('label', $category)) {
            $cate_list = array_merge($cate_list, $label_array);
        }
        if (in_array('director', $category)) {
            $cate_list = array_merge($cate_list, $director_array);
        }
        if (in_array('manufacture', $category)) {
            $cate_list = array_merge($cate_list, $manufacture_array);
        }
        if($cate_other && $cate_free){
            $cate_list = array_merge($cate_list, explode(',', $cate_free));
        }
        $cate_list = array_merge($cate_list, $ex_category);

        // post_tags
        $tag_list = array();
        if (in_array('jan', $tags)) {
            $tag_list = array_merge($tag_list, $genres_array);
        }
        if (in_array('act', $tags)) {
            $tag_list = array_merge($tag_list, $actress_array);
            $tag_list = array_merge($tag_list, $actor_array);
        }
        if (in_array('seri', $tags)) {
            $tag_list = array_merge($tag_list, $series_array);
        }
        if (in_array('author', $tags)) {
            $tag_list = array_merge($tag_list, $author_array);
        }
        if (in_array('maker', $tags)) {
            $tag_list = array_merge($tag_list, $maker_array);
        }
        if (in_array('label', $tags)) {
            $tag_list = array_merge($tag_list, $label_array);
        }
        if (in_array('director', $tags)) {
            $tag_list = array_merge($tag_list, $director_array);
        }
        if (in_array('manufacture', $tags)) {
            $tag_list = array_merge($tag_list, $manufacture_array);
        }
        if($tag_other && $tag_free){
            $tag_list = array_merge($tag_list, explode(',', $tag_free));
        }
        $tag_list = array_merge($tag_list, $ex_tags);
        $tag_list = array_values(array_filter($tag_list));

        // $this->dump($tag_list);
        if((count($tag_list) == 1) && ($tag_list[0] == '----')) $tag_list = array();

        // thumbnail
        $post_thumbnail = $IMG_DIR.$img_name;

        $result = $this->make_post($post, $cate_list, $tag_list, $post_thumbnail);
        if ( $result === '') {

        } else {
            $this->out_flg = TRUE;
            $admin_post_url = admin_url('post.php');
            // $this->complete .='<li>'."<a href=\"{$admin_post_url}?post={$result}&action=edit\">". $cont_title . '<br /><img src="'.$IMG_URL.$img_name.'" width="200px" /></a></li>';
            // $this->complete .='<li>'."<a href=\"{$admin_post_url}?post={$result}&action=edit\" target='_blank'>Title: ". $cont_title . '</a> '.get_permalink($result).'</li>';
            $this->complete .='<li>'."<a href='".get_permalink($result)."' target='_blank'>Title: ". $cont_title . '</a></li>';
        }

    }

    /**
     * Post process
     */
    function make_post($post, $category, $tags, $post_thumbnail) {
        kses_remove_filters();
        $id = wp_insert_post( $post );
        kses_init_filters();

        if ($id) {
            $filetype = wp_check_filetype( basename( $post_thumbnail ), null );
            $wp_upload_dir = wp_upload_dir();
            $attachment = array(
                'guid'           => $wp_upload_dir['url'] . '/' . basename( $post_thumbnail ), 
                'post_mime_type' => $filetype['type'],
                'post_title'     => preg_replace( '/\.[^.]+$/', '', basename( $post_thumbnail ) ),
                'post_content'   => '',
                'post_status'    => 'inherit'
            );
            $attach_id = wp_insert_attachment( $attachment, $post_thumbnail, $id );
            require_once( ABSPATH . 'wp-admin/includes/image.php' );
            $attach_data = wp_generate_attachment_metadata( $attach_id, $post_thumbnail );
            wp_update_attachment_metadata( $attach_id, $attach_data );

            set_post_thumbnail( $id, $attach_id );
            if ($category[0] != "") {
                wp_set_object_terms($id, null, 'category');
                wp_add_object_terms($id, $category, 'category');
			}else{
                $category = array(get_the_category_by_ID(get_option('default_category')));
                wp_set_object_terms($id, $category, 'category');
            }

			if ($tags) {
			    wp_set_post_terms($id, $tags, 'post_tag', true);
			}
        }
        return $id;
    }

    /**
     * HTML List
     */
    function make_list($title, $array, $category, $tags, $word) {
        $return_value = "<li>{$title} : ";
        // echo("<pre>");
        // var_dump($array);
        // echo("</pre>");
        foreach($array as $id => $value) {
            $link = sanitize_title($value->name);
            if($link != '') {
                if(in_array($word, $category)) {
                    $return_value .= "<a href=\"".home_url()."/category/{$link}/\">{$value->name}</a>　";
                } elseif(in_array($word, $tags)) {
                    $return_value .= "<a href=\"".home_url()."/tag/{$link}/\">{$value->name}</a>　";
                } else {
                    $return_value .= "{$value->name}　";
                }
            }
        }
        $return_value .= '</li>';
        return $return_value;
    }

    /**
     * HTML Table
     */
    function make_table($title, $array, $category, $tags, $word) {
        $return_value = "<tr><th>{$title}</th><td>";
        foreach($array as $id => $value) {
            $link = sanitize_title($value->name);
            if($link != '') {
                if(in_array($word, $category)) {
                    $return_value .= "<a href=\"".home_url()."/category/{$link}/\">{$value->name}</a>　";
                } elseif(in_array($word, $tags)) {
                    $return_value .= "<a href=\"".home_url()."/tag/{$link}/\">{$value->name}</a>　";
                } else {
                    $return_value .= "{$value->name}　";
                }
            }
        }
        $return_value .= "</td></tr>";
        return $return_value;
    }

    /**
     * Fanza floor
     */
    function make_floor() {
        $api_id = get_option(self::DB_PREFIX . 'api_id');
        $aff_id = get_option(self::DB_PREFIX . 'aff_id');

        // if($api_id == '') {
        //     $api_id = '';
        //     $aff_id = '';
        // }   

        // request URL
        $url = "https://api.dmm.com/affiliate/v3/FloorList?api_id={$api_id}&affiliate_id={$aff_id}&output=json";

        // get contents
        $response = '';
        $code = '';
        $curl = curl_init();
        $option = [
            CURLOPT_URL => $url,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_CONNECTTIMEOUT => 30,
        ];
        curl_setopt_array($curl, $option);
        $response = curl_exec($curl);
        $code = curl_getinfo($curl,CURLINFO_HTTP_CODE);
 
        curl_close($curl);
        $item_list = json_decode($response);
    
        // Judgment
        $dmm_id_is = 'ERROR';
        switch($code) {
            case 200:
                $dmm_id_is = 'OK';
                break;
            case 400:
                $this->complete .= "<b><p style=\"color:red;\">「DMM API ID」「DMM アフィリエイトID」を正しく設定してください。</p></b>";
                $this->complete .= "<p style=\"color:red;\">[400 error: リクエストが不正です]</p>";
                break;
            case 404:
                $this->complete .= "<p style=\"color:red;\">[404 error: 指定したページが見つかりませんでした]</p>";
                break;
            case 500:
                $this->complete .= "<p style=\"color:red;\">[500 error: 指定したページがあるサーバーにエラーがあります</p>";
                break;
            default:
                $this->complete .= "<p style=\"color:red;\">[error: 何らかのエラーによって指定したページのデータを取得できませんでした]</p>";
        }

        if(isset($item_list->result->site)){

            $sites = $item_list->result->site;
            $site_name = '';
            $site_code = '';
            $service_name = '';
            $service_code = '';
            foreach($sites as $site) {
                $site_name = $site->name;
                if(str_contains($site_name, "DMM.com")) continue;
    
                $site_code = $site->code;
                foreach($site->service as $services) {
                    $service_name = $services->name;
                    $service_code = $services->code;
                    foreach($services->floor as $floor) {
                        $this->floor_array[] = [$site_name, $site_code, $service_name, $service_code, $floor->name, $floor->code];
                    }
                }
            }


        }


        update_option(self::DB_PREFIX . 'dmm_id_is', $dmm_id_is);
    }

    /**
     * HTML Actress
     */
    function make_act_html($lists) {
        $actress_list = '';
        $actress_table = '';
        foreach ($lists as $list) {
            $actress_list .= '<!-- wp:heading {"level":4} -->'."\n<h3>【プロフィール】".$list->name."</h3>\n".'<!-- /wp:heading -->'."\n";
            $actress_table .= '<!-- wp:heading {"level":4} -->'."\n<h3>【プロフィール】".$list->name."</h3>\n".'<!-- /wp:heading -->'."\n";
            $large_img = "";
            $small_img = "";
            $actress_table .= '<table><tr>';
            if(isset($list->imageURL)){
                $large_img = $list->imageURL->large;
                $large_img = str_replace('http://','https://',$large_img);
                $small_img = $list->imageURL->small;
                $small_img = str_replace('http://','https://',$small_img);
                if(isset($large_img)) {
    
                    $actress_list .= '<div class="wp-block-media-text alignwide is-stacked-on-mobile is-vertically-aligned-top" style="grid-template-columns:30% auto"><figure class="wp-block-media-text__media">'."\n";
                    $actress_list .= '<a href="'. $list->listURL->digital .'" target="_blank">';
                    $actress_list .= '<img src="'.$large_img.'" alt="'.$list->name.'" width="200" height="200" /></a></figure><div class="wp-block-media-text__content">'."\n";
                    $actress_table .= '<td>';
                    $actress_table .= '<figure class="wp-block-media-text__media">'."\n";
                    $actress_table .= '<a href="'. $list->listURL->digital .'" target="_blank">';
                    $actress_table .= '<img src="'.$large_img.'" alt="'.$list->name.'" width="200" height="200" /></a></figure>'."\n";
                    $actress_table .= '</td>';
                } elseif(isset($small_img)) {
    
                    $actress_list .= '<div class="wp-block-media-text alignwide is-stacked-on-mobile is-vertically-aligned-top"><figure class="wp-block-media-text__media">'."\n";
                    $actress_list .= '<a href="'. $list->listURL->digital .'" target="_blank">';
                    $actress_list .= '<img src="'.$small_img.'" alt="'.$list->name.'" width="200" height="200" /></a></figure><div class="wp-block-media-text__content">'."\n";
                    $actress_table .= '<td>';
                    $actress_table .= '<figure class="wp-block-media-text__media">'."\n";
                    $actress_table .= '<a href="'. $list->listURL->digital .'" target="_blank">';
                    $actress_table .= '<img src="'.$small_img.'" alt="'.$list->name.'" width="200" height="200" /></a></figure>'."\n";
                    $actress_table .= '</td>';
                }
            }
            $actress_list .= '<ul>';
            $actress_table .= '<td>';
            
            if(isset($list->bust)) {
                if(isset($list->cup)) {
                    $actress_list .= '<li>バスト : '.$list->bust.'cm（'.$list->cup.'カップ）</li>';
                    $actress_table .= 'バスト : '.$list->bust.'cm（'.$list->cup.'カップ）<br>';
                } else {
                $actress_list .= '<li>バスト : '.$list->bust.'cm</li>';
                $actress_table .= 'バスト : '.$list->bust.'cm<br>';
                }
            } else {
                $actress_list .= '<li>バスト : ヒミツ♡</li>';
                $actress_table .= 'バスト : ヒミツ♡<br>';
            }
            
            if(isset($list->waist)) {
                $actress_list .= '<li>ウエスト : '.$list->waist.'cm</li>';
                $actress_table .= 'ウエスト : '.$list->waist.'cm<br>';
            } else {
                $actress_list .= '<li>ウエスト : ヒミツ♡</li>';
                $actress_table .= 'ウエスト : ヒミツ♡<br>';
            }
            if(isset($list->hip)) {
                $actress_list .= '<li>ヒップ : '.$list->hip.'cm</li>';
                $actress_table .= 'ヒップ : '.$list->hip.'cm<br>';
            } else {
                $actress_list .= '<li>ヒップ : ヒミツ♡</li>';
                $actress_table .= 'ヒップ : ヒミツ♡<br>';
            }
            if(isset($list->height)) {
                $actress_list .= '<li>身長 : '.$list->height.'cm</li>';
                $actress_table .= '身長 : '.$list->height.'cm<br>';
            }
            if(isset($list->birthday)) {
                $actress_list .= '<li>誕生日 : '.$list->birthday.'</li>';
                $actress_table .= '誕生日 : '.$list->birthday.'<br>';
            }
            if(isset($list->blood_type)) {
                $actress_list .= '<li>血液型 : '.$list->blood_type.'型</li>';
                $actress_table .= '血液型 : '.$list->blood_type.'型<br>';
            }
            if(isset($list->hobby)) {
                if($list->hobby != '') {
                    $actress_list .= '<li>趣味 : '.$list->hobby.'</li>';
                    $actress_table .= '趣味 : '.$list->hobby.'<br>';
                }else{
                    $actress_list .= '<li>趣味 : ヒミツ♡</li>';
                    $actress_table .= '趣味 : ヒミツ♡<br>';
                }
            }
            if(isset($list->prefectures)) {
                if($list->prefectures != '') {
                    $actress_list .= '<li>出身地 : '.$list->prefectures.'</li>';
                    $actress_table .= '出身地 : '.$list->prefectures.'<br>';
                }else{
                    $actress_list .= '<li>出身地 : ヒミツ♡</li>';
                    $actress_table .= '出身地 : ヒミツ♡<br>';
                }
            }
            $actress_list .= '<li><a href="'. $list->listURL->digital .'" target="_blank">'.$list->name."の作品一覧</a></li>";
            $actress_table .= '<a href="'. $list->listURL->digital .'" target="_blank">'.$list->name."の作品一覧</a><br>";
            $actress_list .= '</ul>'."\n";
            $actress_table .= '</td></tr></table>'."\n";
            if($large_img != '' || $small_img != '') {
                $actress_list .= '</div></div>'."\n";
            } 
           
        }
        return [$actress_list, $actress_table];
    }

    /**
     * API GET
     */
    function curl_get_list($url) {
        // get contents
        $response = '';
        $code = '';
        $curl = curl_init();
        $option = [
            CURLOPT_URL => $url,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_CONNECTTIMEOUT => 30,
        ];
        curl_setopt_array($curl, $option);
        $response = curl_exec($curl);
        $code = curl_getinfo($curl,CURLINFO_HTTP_CODE);
 
        curl_close($curl);
        $item_list = json_decode($response);

        // Judgment
        switch($code) {
            case 200:
                break;
            case 400:
                $this->complete .= "<p style=\"color:red;\">リクエストが不正です</p>";
                break;
            case 404:
                $this->complete .= "<p style=\"color:red;\">指定したページが見つかりませんでした</p>";
                break;
            case 500:
                $this->complete .= "<p style=\"color:red;\">指定したページがあるサーバーにエラーがあります</p>";
                break;
            default:
                $this->complete .= "<p style=\"color:red;\">何らかのエラーによって指定したページのデータを取得できませんでした</p>";
        }
        $lists = "";
        if (isset($item_list->result->items)) {
            $lists = $item_list->result->items;
        } elseif (isset($item_list->result->actress)) {
            $lists = $item_list->result->actress;
        }
        return $lists;
    }

    function curl_get_list2($url, $offset, $hits, $lists_recent) {

        // get contents
        $response = '';
        $code = '';
        $curl = curl_init();
        $option = [
            CURLOPT_URL => $url."&offset=".$offset."&hits=100",
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_CONNECTTIMEOUT => 30,
        ];
        curl_setopt_array($curl, $option);
        $response = curl_exec($curl);
        $code = curl_getinfo($curl,CURLINFO_HTTP_CODE);
 
        curl_close($curl);
        $item_list = json_decode($response);

        // $this->auto_process_log("code : ".$code);
        // $this->auto_process_log("hits : ".$hits);

        // Judgment
        switch($code) {
            //200 success
            case 200:
                break;
            //400 bad request
            case 400:
                $this->complete .= "<p style=\"color:red;\">リクエストが不正です。入力値を確認して下さい。</p>";
                break;
            //404 error
            case 404:
                $this->complete .= "<p style=\"color:red;\">指定したページが見つかりませんでした</p>";
                break;
            //500 error
            case 500:
                $this->complete .= "<p style=\"color:red;\">指定したページがあるサーバーにエラーがあります</p>";
                break;
            // other error
            default:
                $this->complete .= "<p style=\"color:red;\">何らかのエラーによって指定したページのデータを取得できませんでした</p>";
        }
        // if (isset($item_list->result->items)) {
        //     $lists = $item_list->result->items;
        // } else {
        //     $lists = $item_list->result->actress;
        // }

        $result_count = $item_list->result->result_count;
        $total_count = $item_list->result->total_count;
        // echo '<script>console.log("'.$total_count.'");</script>';
        // echo '<script>console.log("'.$result_count.'");</script>';

        // $this->auto_process_log("result_count: ".$result_count);
        // $this->auto_process_log("total_count: ".$total_count);


        if($result_count == 0) return [[],"",$total_count];

        // echo "<script type=\"text/javascript\">console.log(\"{$result_count}\");</script>";
        // echo '<script>console.log("'.$result_count.'");</script>';

        global $wpdb;
        $duplicate = '';
        
        // var_dump("item_list");
        // var_dump(count($item_list->result->items));

        $total_list = [];
        $table_prefix = $wpdb->prefix;
        $inum = 0;
        $duplicate_count = 0;
        foreach ($item_list->result->items as $item) {
            // var_dump("---------------------------------------------------------");
            // echo('<pre>');
            // var_dump($item);
            // echo('</pre>');
            $query = "SELECT post_name FROM {$table_prefix}posts WHERE post_name ='{$item->content_id}'";
            $id='';
            // Next if title is the same
            $result = $wpdb->get_results($query, OBJECT);
            foreach ($result as $row) {
                    $id = $row->post_name;
            }
            if ($id == $item->content_id) {
                // var_dump("[".$inum."]");
                $duplicate_count++;
                continue;
            }

            $total_list[] = $item;
            $inum++;

            $remain_hits = $hits - count($total_list);
            // $this->auto_process_log("get [".$inum."/".count($total_list)."] " . " remain_hits: ".$remain_hits." content_id: " . $item->content_id );

            if($inum > $hits-1) break;
        }

        $total_list = array_merge($lists_recent, $total_list);
        // $this->auto_process_log("total_list A: ".count($total_list));
        $total_list = array_unique($total_list, SORT_REGULAR);
        // $this->auto_process_log("total_list B: ".count($total_list));


        // var_dump("total_list");
        // var_dump(count($total_list));

        // $recursive_list = [];
        // echo '<script>console.log("'.count($total_list).'");</script>';
        // echo '<script>console.log("'.$hits.'");</script>';

        // 例：total_count:50  result_count:50  hits:100 count_total_list: 48
        // 例：total_count:150  result_count:100  hits:100 count_total_list: 98
        // 例：total_count:250  result_count:100  hits:100 count_total_list: 98

        if(count($total_list) < $hits){
            if($total_count > ($offset - 1 + $result_count)){
                // echo '<script>console.log("'.$total_count.'");</script>';
                // echo '<script>console.log("'.($offset - 1 + $result_count).'");</script>';
                // echo '<script>console.log("取得データがhitsに満たない、かつtotal_countにまだ余裕があるので追加取得");</script>';

                // $this->auto_process_log("remain hits : ".($hits - count($total_list)));

                list($recursive_list, $duplicate_count_add, $total_count) = $this->curl_get_list2($url, $offset+100, $hits, $total_list);
                $duplicate_count = $duplicate_count + $duplicate_count_add;
                $total_list = $recursive_list;
                // $total_list = array_merge($total_list, $recursive_list);
                // // $total_list[] = $recursive_list;

                // $this->auto_process_log("total_list 1: ".count($total_list));
                // $total_list = array_unique($total_list, SORT_REGULAR);
                // $this->auto_process_log("total_list 2: ".count($total_list));

            }
  
        }elseif(count($total_list) > $hits){
            // $this->auto_process_log("total_list X: ".count($total_list));
            $total_list = array_slice($total_list, 1, $hits);
            // $this->auto_process_log("total_list Y: ".count($total_list));
        }

        return [$total_list, $duplicate_count, $total_count];
    }


    function fanza_auto_vartag() {
    ?>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/css/bootstrap.min.css" integrity="sha384-GJzZqFGwb1QTTN6wy59ffF1BuGJpLSa9DkKMp0DgiMDm4iYMj70gZWKYbI706tWS" crossorigin="anonymous">

        <h2>FANZA Auto大量投稿プラグイン | 変数タグ一覧</h2>
        <hr>
        <h3>文字パーツ</h3>
    
                    <table class="table table-striped table-bordered" style="width:99%;">
                        <thead style="color:white; background-color:black;">
                            <tr>
                            <th scope="col" width="50%">表示内容</th>
                            <th scope="col">変数タグ</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                            <td>作品タイトル</td>
                            <td>[title]</td>
                            </tr>
                            <tr>
                            <td>作品ID</td>
                            <td>[cid]</td>
                            </tr>

                            <tr>
                            <td>女優名</td>
                            <td>[actress]</td>
                            </tr>
                            <tr>
                            <td>出演者</td>
                            <td>[performer]</td>
                            </tr>
                            <tr>
                            <td>メーカー名</td>
                            <td>[maker]</td>
                            </tr>
                            <tr>
                            <td>レーベル名</td>
                            <td>[label]</td>
                            </tr>
                            <tr>
                            <td>出版社</td>
                            <td>[publisher]</td>
                            </tr>
                            <tr>
                            <td>監督名</td>
                            <td>[director]</td>
                            </tr>
                            <tr>
                            <td>シリーズ名</td>
                            <td>[series]</td>
                            </tr>
                            <tr>
                            <td>作者</td>
                            <td>[author]</td>
                            </tr>
                            <tr>
                            <td>動画分数・音声分数・漫画枚数</td>
                            <td>[volume]</td>
                            </tr>
                            <tr>
                            <td>発売日</td>
                            <td>[date]</td>
                            </tr>
                            <tr>
                            <td>ジャンル</td>
                            <td>[genre]</td>
                            </tr>

                            <tr>
                            <td>レビュー数</td>
                            <td>[review-count]</td>
                            </tr>
                            <tr>
                            <td>レビュー平均点</td>
                            <td>[review-average]</td>
                            </tr>

                            <tr>
                            <td>ランダムテキスト1</td>
                            <td>[random1]</td>
                            </tr>
                            <tr>
                            <td>ランダムテキスト2</td>
                            <td>[random2]</td>
                            </tr>
                            <tr>
                            <td>ランダムテキスト3</td>
                            <td>[random3]</td>
                            </tr>
                            
                            <tr style="background-color: #e8f5e8;">
                            <td><strong>LLM生成コンテンツ（新機能）</strong></td>
                            <td><strong>AIによる自動生成</strong></td>
                            </tr>
                            <tr>
                            <td>LLM生成紹介文</td>
                            <td>[llm_intro]</td>
                            </tr>
                            <tr>
                            <td>LLM生成SEOタイトル</td>
                            <td>[llm_seo_title]</td>
                            </tr>
                            <tr>
                            <td>LLM生成改善コンテンツ</td>
                            <td>[llm_enhance]</td>
                            </tr>

                        </tbody>
    </table>

    <h3>HTMLパーツ</h3>

    <table class="table table-striped table-bordered" style="width:99%;">
                        <thead style="color:white; background-color:black;">
                            <tr>
                            <th scope="col" width="50%">表示内容</th>
                            <th scope="col">変数タグ</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                            <td>作品詳細(リスト)</td>
                            <td>[detail-list]</td>
                            </tr>
                            <tr>
                            <td>作品詳細(テーブル)</td>
                            <td>[detail-table]</td>
                            </tr>
                            <tr>
                            <td>パッケージ画像</td>
                            <td>[package]</td>
                            </tr>
                            <tr>
                            <td>サンプル動画(大)</td>
                            <td>[sample-movie2]</td>
                            </tr>
                            <tr>
                            <td>サンプル動画(小)</td>
                            <td>[sample-movie]</td>
                            </tr>
                            <tr>
                            <td>立ち読みボタン</td>
                            <td>[tachiyomi]</td>
                            </tr>

                            <tr>
                            <td>サンプル画像(キャプションあり)</td>
                            <td>[sample-cap]</td>
                            </tr>
                            <tr>
                            <td>サンプル画像(キャプションなし)</td>
                            <td>[sample-photo]</td>
                            </tr>
                            <tr>
                            <td>サンプル画像(横並び)</td>
                            <td>[sample-flex]</td>
                            </tr>
                            <tr>
                            <td>女優情報(リスト)</td>
                            <td>[act-info]</td>
                            </tr>
                            <tr>
                            <td>女優情報(テーブル)</td>
                            <td>[act-table]</td>
                            </tr>
                            <tr>
                            <td>作品詳細説明</td>
                            <td>[comment]</td>
                            </tr>
                            <tr>
                            <td>作品詳細説明（短縮版）</td>
                            <td>[comment-short]</td>
                            </tr>
                            <tr>
                            <td>アフィリエイトリンクボタン</td>
                            <td>[aff-button]</td>
                            </tr>
                            <tr>
                            <td>アフィリエイトリンクボタン2</td>
                            <td>[aff-button2]</td>
                            </tr>

                            <tr>
                            <td>レビュー表示<br>例：<img src="https://p.dmm.co.jp/p/ms/review/4_5.gif" />&nbsp;<span style='font-size: 80%;'>4.6</span><br>例：<img src="https://p.dmm.co.jp/p/ms/review/0.gif" />&nbsp;<span style='font-size: 80%;'>-</span></td>
                            <td>[review]</td>
                            </tr>
                            <tr>
                            <td>レビュー表示2<br>例：<img src="https://p.dmm.co.jp/p/ms/review/4_5.gif" />&nbsp;<span style='font-size: 80%;'>4.6</span><br>（※無評価は非表示）</td>
                            <td>[review2]</td>
                            </tr>

                            <tr>
                            <td>アフィリエイトリンクURL</td>
                            <td>[aff-link]</td>
                            </tr>
                            <tr>
                            <td>立ち読みリンクURL</td>
                            <td>[tachiyomi-link]</td>
                            </tr>

                        </tbody>
                    </table>


    
    <?php
    }
    
    function disp_post_settings($set_menu_number){
        $number = "";
        if($set_menu_number != "1") $number = $set_menu_number.'_';
        $template_number = "";
        if($set_menu_number != "1") $template_number = $set_menu_number;

        $hits       = get_option(self::DB_PREFIX . $number . 'hits');
        $flr_name   = get_option(self::DB_PREFIX . $number . 'flr_name');
        $keyword    = get_option(self::DB_PREFIX . $number . 'keyword');
        $article_type = get_option(self::DB_PREFIX . $number . 'article_type');
        $article_id   = get_option(self::DB_PREFIX . $number . 'article_id');
        $sort       = get_option(self::DB_PREFIX . $number . 'sort');
        $from_date  = get_option(self::DB_PREFIX . $number . 'from_date');
        $to_date    = get_option(self::DB_PREFIX . $number . 'to_date');
        $t_title    = get_option(self::DB_PREFIX . $number . 't_title');
        $output     = get_option(self::DB_PREFIX . $number . 'output');

        global $wpdb;
        $table_prefix = $wpdb->prefix;
        $query = "SELECT id, post_content FROM {$table_prefix}posts WHERE post_title ='FANZAテンプレート".$template_number."' && post_type='post' && post_status = 'draft' ORDER BY post_date desc limit 1";
        $template_id = '';
        $result = $wpdb->get_results($query, OBJECT);
        foreach ($result as $row) {
                $template_id = $row->id;
        }  
        
        ?>

                            <tr>
                            <th>投稿設定<?= $set_menu_number ?></th>
                            <td>
                                投稿タイトルテンプレート指定： <span style='color:#00CC00;'><b><?= $t_title ?></b></span><br>
                                投稿本文テンプレート指定： <?php if($template_id){ echo("<span style='color:#00CC00;'><b>あり</b></span>");}else{echo("<span style='color:red;'><b>なし</b></span>");} ?><br>
                                投稿キーワード指定： <span style='color:#00CC00;'><b><?= $keyword ?></b></span><br>
                                フロア指定： <span style='color:#00CC00;'><b><?= $flr_name ?></b></span><br>
                                検索/投稿件数指定： <?php if($hits){echo("<span style='color:#00CC00;'><b>".$hits."</b></span>");}else{echo("<span style='color:red;'><b>未指定</b></span>");} ?>（※重複を除外した上で指定数まで投稿）<br>
                                ソート順指定： 
                                <?php
                                echo("<span style='color:#00CC00;'><b>");
                                if($sort=="rank") echo('人気順');
                                if($sort=="date") echo('新着順');
                                if($sort=="review") echo('評価順');
                                if($sort=="price") echo('価格が高い順');
                                echo("</b></span>");
                                ?>
                                <br>
                                発売日絞り込み： [<?php if($from_date){echo($from_date);}else{echo('----');} ?>]～[<?php if($to_date){echo($to_date);}else{echo('----');} ?>]　（※自動実行時は無視）<br>
                                投稿ステータス： <?php if($output=="publish"){echo("<span style='color:#00CC00;'><b>公開（publish）</b></span>");}else{echo("<span style='color:#00CC00;'><b>下書き（draft）</b></span>");} ?>

                            </td>
                            </tr>
        <?php
    }

    function fanza_auto_set() {
        $dmm_id_is  = get_option(self::DB_PREFIX . 'dmm_id_is');

        // ------------------------------------------------------- //
        $exe_hour   = get_option(self::DB_PREFIX . 'exe_hour');
        $hour_list  = explode('/', $exe_hour);
        $today      = get_option(self::DB_PREFIX . 'today');
        $threeday   = get_option(self::DB_PREFIX . 'threeday');
        $range      = get_option(self::DB_PREFIX . 'range');
        $s_date     = get_option(self::DB_PREFIX . 's_date');
        $e_date     = get_option(self::DB_PREFIX . 'e_date');
        if($s_date == '') $s_date = date_i18n("Y-m-d");
        if($e_date == '') $e_date = date_i18n("Y-m-d");
        $exe_min    = get_option(self::DB_PREFIX . 'exe_min');
        if(!$exe_min) $exe_min = $this->generate_unique_num(gethostname());
        $exe_select = get_option(self::DB_PREFIX . 'exe_select');
        $select_list  = "";
        if($exe_select) $select_list  = explode('/', $exe_select);
        $auto_on    = get_option(self::DB_PREFIX . 'auto_on');
        if(!$auto_on) $auto_on = "off";
        $api_id     = get_option(self::DB_PREFIX . 'api_id');
        $aff_id     = get_option(self::DB_PREFIX . 'aff_id');



        $hookB = 'fanza_autoB_hook';
        $args = array();
        $res_timestampB = as_next_scheduled_action($hookB, $args, '');

        $next_schedule = "--";
        if($res_timestampB === true){
            $next_schedule = "(処理実行中)";
        }elseif($res_timestampB){
            $timezone = (strtotime(date_i18n("Y-m-d H:i:s")) - strtotime(date("Y-m-d H:i:s")))/3600;
            $next_schedule = date_i18n("Y-m-d H:i:s", strtotime('+'.$timezone.' hours', $res_timestampB));
        }

        // YYY
        ?>

        <script src="/wp-content/plugins/<?= self::PLUGIN_NAME ?>/includes/jquery.shiftcheckbox.js"></script>
        <script>
        jQuery(function () {
            jQuery('.checkboxgroup').shiftcheckbox();
        });
        </script>

        <h2>FANZA Auto大量投稿プラグイン | 自動実行ON-OFF</h2>

        <?php
            if($dmm_id_is != 'OK'){
                echo("<p>先に有効なDMM IDをセットしてください→[<a href='".admin_url('admin.php')."?page=fanza-auto-menu1'>投稿設定ページへ</a>]</p>");
                return;
            }
        ?>

        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/css/bootstrap.min.css" integrity="sha384-GJzZqFGwb1QTTN6wy59ffF1BuGJpLSa9DkKMp0DgiMDm4iYMj70gZWKYbI706tWS" crossorigin="anonymous">

        <table border="1" style="border: 15px solid black; border-collapse: collapse; color:white; background-color:black; width:99%;">
            <tr><td>現状設定参照</td></tr>
        </table>
        <table class="table table-bordered" style="width:99%;">
                        <tbody>
                            <tr>
                            <th width="25%">自動実行</th>
                            <td><?= $auto_on ?></td>
                            </tr>

                            <tr>
                            <th>次回自動投稿　実行時刻</th>
                            <td><?= $next_schedule ?></td>
                            </tr>

                            <tr>
                            <th>自動実行設定</th>
                            <td>
                                <?php
                                echo("■投稿対象（発売日絞り込み）<br>");
                                if($today || $threeday ||$range){
                                    if($today){echo("・本日<br>");}
                                    if($threeday){echo("・1日前～3日前<br>");}
                                    if($range){echo("・[".$s_date."]～[".$e_date."]<br>");}


                                }else{
                                    echo("--");
                                }

                                echo("<br>■処理開始時刻<br>");
                                if($exe_hour){
                                    $exe_i = 0;
                                    foreach($hour_list as $hour){
                                        $exe_i++;
                                        $hnum = str_replace('h0','',$hour);
                                        $hnum = str_replace('h','',$hnum);
                                        $select_one = "1";
                                        if($select_list) $select_one = $select_list[$hnum];
                                        echo("[".str_replace('h','',$hour).":".sprintf('%02d', $exe_min)."](".$select_one.")&nbsp;&nbsp;&nbsp;");
                                        if($exe_i%6==0) echo("<br>");

                                    }
                                }else{
                                    echo("--");
                                }


                                ?>
                            </td></tr>

        <?php
            $this->disp_post_settings("1");
            $this->disp_post_settings("2");
            $this->disp_post_settings("3");
            $this->disp_post_settings("4");
        ?>

                        </tbody>
        </table>
        <br>

        <table border="1" style="border: 15px solid black; border-collapse: collapse; color:white; background-color:black; width:99%;">
            <tr><td>自動実行を設定する</td></tr>
        </table>

        <form action="?" method="POST" id="fanza-auto-menu">
        <?php wp_nonce_field(self::NONCE_ACTION, self::NONCE_FIELD) ?>
        <table class="table table-bordered" style="width:99%;">
                        <tbody>
                            <tr>
                            <th width="25%">自動実行ON/OFF</th>
                            <td><input type="radio" name="auto_on" value="on" <?php if($auto_on=="on"){echo("checked");}?> ><span style="">ON</span>&nbsp;&nbsp;&nbsp;&nbsp;<input type="radio" name="auto_on" value="off" <?php if($auto_on=="off"){echo("checked");}?> ><span style="">OFF</span></td>
                            </tr>

                            <tr>
                            <th>投稿対象<br>※「発売日絞り込み」<br>※ [直近分]を投稿し切ってから[過去分]を実行</th>
                            <td>
                                ■[直近分]　以下の期間に発売された作品を投稿対象とする<br>
                                &nbsp;&nbsp;<input type="checkbox" name="today" id="today" value="1" <?php if($today){echo("checked");}?> >本日&nbsp;&nbsp;
                                <input type="checkbox" name="threeday" id="threeday" value="1" <?php if($threeday){echo("checked");}?> >1日前～3日前&nbsp;&nbsp;
                                <br><br>
                                ■[過去分]　以下の期間に発売された作品を投稿対象とする<br>
                                &nbsp;&nbsp;<input type="checkbox" name="range" id="range" value="1" <?php if($range){echo("checked");}?> >
                                <input type="date" name="s_date" id="s_date" value="<?= $s_date ?>">～<input type="date" name="e_date" id="e_date" value="<?= $e_date ?>"><br>
                                （※DMM APIの検索結果上限は5万件）<br>（※検索結果が1万以上になると巡回の負荷が増えるため、絞り込んだ期間設定を推奨）<br>



                            
                            </td>
                            </tr>

                            <tr>
                            <th>実行時刻[時間]</th>
                            <td>


                            <?php
                                echo $this->make_hour_check_box($this->hour_ary, $hour_list, $select_list);
                            ?>


                            </td>
                            </tr>

                            <tr>
                            <th>実行時刻[分]</th>
                            <td><input type="number" name="exe_min" id="exe_min" pattern="^[0-9]+$" min="0" max="59" value="<?= $exe_min ?>"></td>
                            </tr>

                        </tbody>
        </table>

        <button type="submit" name="fanza_auto_hour_submit" value="1" class="btn btn-primary" onclick="return vCheck();" formaction="<?=  admin_url('admin.php') ?>?page=fanza-auto-plugin-menu">設定保存</button>
        <input type="hidden" id="api_id" value="<?= $api_id ?>" />

        </form>

<script>
    function vCheck(){
        if((jQuery("#s_date").val() == '') || (jQuery("#e_date").val() == '')){
            alert("絞り込み期間の日付を範囲指定してください");
            return false;
        }else{
            // $start = new Date(jQuery("#s_date").val()).getTime();
            // $end = new Date(jQuery("#e_date").val()).getTime();
            // $between = ($end - $start)/1000/86400;
            // if($between > 366){
            //     alert("期間の範囲は1年以内で指定してください");
            //     return false;
            // }

            $api_id = jQuery("#api_id").val();
            if($api_id == ''){
                if(jQuery("[name=auto_on]:checked").val() == "on"){
                    jQuery("[name=auto_on]").val("off");
                    alert("DMM ID が正しく指定されていないため、自動実行をOFFにします");
                }
            }

            $today = jQuery("#today:checked").val();
            $threeday = jQuery("#threeday:checked").val();
            $range = jQuery("#range:checked").val();

            if(!$today && !$threeday && !$range){
                if(jQuery("[name=auto_on]:checked").val() == "on"){
                    jQuery("[name=auto_on]").val("off");
                    alert("投稿対象 が無選択のため、自動実行をOFFにします");
                }
            }

            $check_i = 0;
            jQuery('input[name^="hour_list"]:checked').each(function(){
                $check_i++;
            })
            if($check_i == 0){
                if(jQuery("[name=auto_on]:checked").val() == "on"){
                    jQuery("[name=auto_on]").val("off");
                    alert("実行時刻[時間] が無選択のため、自動実行をOFFにします");
                }
            }

            return true;
        }
    }

</script>

        <?php
    }

    function generate_unique_num($column)
    {
      //文字列→数値変換
      $column = strrev($column);
      $arr_column = str_split($column);
      $column_num = 0;
      for($i = 0; $i < count($arr_column); $i++) {
        $column_num += (ord($arr_column[$i]) -64) * pow(26, $i);
      }
      $num = intval(abs($column_num))%60;
      if($num < 0) $num = $num + 60;
      return $num;
    }

    function createAutoSchedule($auto_on){
        // hookを削除
        $hookA = 'fanza_autoA_hook';
        $hookB = 'fanza_autoB_hook';
        $args = array();
        $res_timestampB = as_next_scheduled_action($hookB, $args, '');

        //hookAがhookBを停止しなければならない可能性に備えてhookAを存続
        if($res_timestampB !== true){ // hookBが処理実行中以外の時のみ unschedule
            as_unschedule_all_actions($hookA);
        }
        as_unschedule_all_actions($hookB); // hookB削除、ただしhookBが処理実行中の時は消されない

        // hookをセット
        if($auto_on=="on"){
            $booleanA = as_has_scheduled_action($hookA);
            if($booleanA === false){ // hookAが「ない」時にhookAを起動（hookA 二重化対策）
                as_schedule_recurring_action(
                    time(), 60, $hookA, $args
                );
            }

            $res_timestampB = as_next_scheduled_action($hookB, $args, '');

            $schedule = $this->createActionSchedule();

            if($res_timestampB === false){ // hookBが存在しない時（hookB 二重化対策）
                // hookB処理を追加
                as_schedule_cron_action( time(), $schedule, $hookB, $args );
            }elseif($res_timestampB === true){
                //hookBが処理実行中の時 YYY
                update_option(self::DB_PREFIX . 'delay_setB', $schedule);
            }
        }
    }

    function createActionSchedule(){
        $hour_cron = "";
        $exe_hour   = get_option(self::DB_PREFIX . 'exe_hour');
        $exe_min    = get_option(self::DB_PREFIX . 'exe_min');
        $hour_list = explode('/', $exe_hour);
        $timezone = (strtotime(date_i18n("Y-m-d H:i:s")) - strtotime(date("Y-m-d H:i:s")))/3600;
        foreach($hour_list as $hour){
            $hour_str = (str_replace('h','',$hour) - $timezone)%24;
            if(str_contains($hour_str,'-')){$hour_str = $hour_str+24;}
            if($hour_cron !== "") $hour_cron .= ',';
            $hour_cron .= strval($hour_str);
        }

        $schedule = $exe_min." ".$hour_cron." * * *";
        return $schedule;
    }

    function fanza_autoA() {
        // フラグを確認する→OFFでOKならreturn
        $args = array();
        $auto_on   = get_option(self::DB_PREFIX . 'auto_on');
        if($auto_on != 'on'){
            // fanza_autoB が起動しているか確認
            $hookB = 'fanza_autoB_hook';
            $res_timestampB = as_next_scheduled_action($hookB, $args, '');
            if($res_timestampB !== true){ // hookBが処理実行中「でない」時
                //auto_on が off なのに 起動している fanza_autoB を unschedule する
                as_unschedule_all_actions($hookB);
            }
            return;
        }

        // fanza_autoB が起動しているか確認
        $hookB = 'fanza_autoB_hook';
        $res_timestampB = as_next_scheduled_action($hookB, $args, '');

        // fanza_autoB が存在しない場合、起動する
        if($res_timestampB === false){
            $schedule = $this->createActionSchedule();
            as_schedule_cron_action(
                time(), $schedule, $hookB, $args
            );

            update_option(self::DB_PREFIX . 'delay_setB', '');
        }elseif(is_int($res_timestampB)){
            $delay_setB   = get_option(self::DB_PREFIX . 'delay_setB');
            if($delay_setB != ''){
                // hookB状態が古いため、登録し直す
                as_unschedule_all_actions($hookB);

                // hookB重複対策
                sleep(1);
                $res_timestampB = as_next_scheduled_action($hookB, $args, '');
                if($res_timestampB === false){
                    as_schedule_cron_action(
                        time(), $delay_setB, $hookB, $args
                    );
                    update_option(self::DB_PREFIX . 'delay_setB', '');    
                }
            }
        }

        // hookB 多重起動していた場合の対策
        $argsB = ['hook' => $hookB, 'status' => 'Pending'];
        $resultB = as_get_scheduled_actions( $argsB );
        $countB = count($resultB);
        // $this->auto_process_log("■count: ".$countB);
        if($countB > 1){
            // hookB 削除
            foreach(range(2,$countB) as $i){
                // $this->auto_process_log('[fanza_autoA] as_unschedule_action(hookB)');
                as_unschedule_action($hookB);    
            }
        }
    }

    // auto exe
    // function create_test_post() {
    function fanza_autoB() {
        ini_set('max_execution_time',900);
        
        // ---------------------------------------------------------- //
        $exe_min    = get_option(self::DB_PREFIX . 'exe_min');
        $exe_select = get_option(self::DB_PREFIX . 'exe_select');
        $select_list = "";
        if($exe_select) $select_list = explode('/', $exe_select);
        
        if(($exe_min == "59") || ($exe_min == "58")){ // min が58分・59分の場合、2分ほど引いた時刻を出す
            $hour_set = date_i18n("G", strtotime("-2 min", current_time('timestamp'))); //先頭0なしの「X時」
        }else{
            $hour_set = date_i18n("G"); //先頭0なしの「X時」
        }
        $set_menu_number = "1";
        if($select_list) $set_menu_number = $select_list[$hour_set];
        
        // $this->auto_process_log("set_menu_number:" . $set_menu_number);

        // ---------------------------------------------------------- //

        list($lists, $service, $floor, $duplicate_count, $total_count) = $this->serch_contents_process("auto", $set_menu_number);

        global $wpdb;
        // end if empty
        if (empty($lists)) {
            return;
        }
        
        $template_number = "";
        if($set_menu_number != "1") $template_number = $set_menu_number;

        // テンプレートを取得
        $table_prefix = $wpdb->prefix;
        $query = "SELECT id, post_content FROM {$table_prefix}posts WHERE post_title ='FANZAテンプレート".$template_number."' && post_type='post' && post_status = 'draft' ORDER BY post_date desc limit 1";
        $template_id = '';
        $post_content = '';
        // Next if title is the same
        $result = $wpdb->get_results($query, OBJECT);
        foreach ($result as $row) {
                $template_id = $row->id;
                $post_content = $row->post_content;
        }            

        // $this->auto_process_log("set_menu_number:" . $set_menu_number);

        $i = 0;
        foreach($lists as $list){
            $i++;
            // $this->auto_process_log("post [".$i."/".count($lists)."] content_id: " . $list->content_id);

            $this->post_contents_process($list, $post_content, $wpdb, "", "", $set_menu_number);
        }

        // $this->complete .='<p>登録完了</p>'; // XXX
        // $this->contents_array = array();
    }
    
    /**
     * Process LLM variable tags
     * 
     * @param string $content Content with LLM tags
     * @param object $list FANZA item data
     * @param string $description Item description
     * @return string Processed content
     */
    private function process_llm_vartags($content, $list, $description) {
        if (!$this->llm_manager) {
            return $content;
        }
        
        // Build metadata for LLM
        $metadata = array(
            'title' => isset($list->title) ? $list->title : '',
            'genre' => isset($list->iteminfo->genre) ? implode(' ', array_column($list->iteminfo->genre, 'name')) : '',
            'actress' => isset($list->iteminfo->actress) ? implode(' ', array_column($list->iteminfo->actress, 'name')) : '',
            'maker' => isset($list->iteminfo->maker) ? implode(' ', array_column($list->iteminfo->maker, 'name')) : '',
            'series' => isset($list->iteminfo->series) ? implode(' ', array_column($list->iteminfo->series, 'name')) : '',
            'director' => isset($list->iteminfo->director) ? implode(' ', array_column($list->iteminfo->director, 'name')) : '',
            'date' => isset($list->date) ? $list->date : ''
        );
        
        // Process [llm_intro] tag
        if (strpos($content, '[llm_intro]') !== false) {
            $intro = $this->llm_manager->generate_introduction($description, $metadata);
            $content = str_replace('[llm_intro]', $intro, $content);
        }
        
        // Process [llm_seo_title] tag
        if (strpos($content, '[llm_seo_title]') !== false) {
            $seo_title = $this->llm_manager->generate_seo_title($metadata['title'], $metadata);
            $content = str_replace('[llm_seo_title]', $seo_title, $content);
        }
        
        // Process [llm_enhance] tag
        if (strpos($content, '[llm_enhance]') !== false) {
            $enhanced = $this->llm_manager->generate_enhanced_content($description, $metadata);
            $content = str_replace('[llm_enhance]', $enhanced, $content);
        }
        
        return $content;
    }

}

if (class_exists('FANZAAuto\FANZAAutoPlugin')) {
    $fanza_auto_plugin = new FANZAAutoPlugin();
}

