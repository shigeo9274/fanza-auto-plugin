<?php
/**
 * Template Engine Test File
 * This file tests the template engine functionality
 */

// Include the main plugin file
require_once 'fanza-auto-plugin.php';

use FANZAAuto\TemplateEngine;
use FANZAAuto\ContentGenerator;

echo "=== Template Engine Test ===\n\n";

// Test TemplateEngine
echo "1. Testing TemplateEngine:\n";
$template_engine = new TemplateEngine();

// Test basic variable replacement
$template_engine->set('title', 'Test Title');
$template_engine->set('aff-link', 'https://example.com');
$template_engine->set('package-image', 'https://example.com/image.jpg');

$result = $template_engine->render('package-image');
echo "Package Image Template Result:\n";
echo $result . "\n\n";

// Test ContentGenerator
echo "2. Testing ContentGenerator:\n";
$content_generator = new ContentGenerator();

// Test package image generation
$package_image = $content_generator->generatePackageImage(
    'https://example.com/image.jpg',
    'https://example.com/affiliate',
    'Test Product',
    '300',
    '400'
);
echo "Generated Package Image:\n";
echo $package_image . "\n\n";

// Test button generation
$button = $content_generator->generateButton(
    1,
    'https://example.com/affiliate',
    'Buy Now',
    '#ffffff',
    '#007cba'
);
echo "Generated Button:\n";
echo $button . "\n\n";

// Test detail table generation
$details = [
    ['label' => 'Title', 'value' => 'Test Product'],
    ['label' => 'Price', 'value' => '¥1000'],
    ['label' => 'Category', 'value' => 'Test Category']
];
$detail_table = $content_generator->generateDetailTable($details);
echo "Generated Detail Table:\n";
echo $detail_table . "\n\n";

echo "=== Test Complete ===\n";
?>
