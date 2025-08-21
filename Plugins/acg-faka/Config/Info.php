<?php
declare (strict_types = 1);

return [
    'version'     => '1.0.0',
    'name'        => '土豆方块支付',
    'author'      => '小虫虫',
    'website'     => 'https://github.com/hyhpdyr/PotatoblockPay',
    'description' => '开源免费，纯本地零费率，支持微信、支付宝、爱发电赞助和Trc20-USDT。使用方式见项目仓库。',
    'options'     => [
        'wxpay'      => '微信支付',
        'alipay'     => '支付宝',
        'afdian'     => '爱发电',
        'trc20.usdt' => 'TRC20·USDT'
    ],
    'callback'    => [
        \App\Consts\Pay::IS_SIGN            => true,
        \App\Consts\Pay::IS_STATUS          => true,
        \App\Consts\Pay::FIELD_STATUS_KEY   => 'status',
        \App\Consts\Pay::FIELD_STATUS_VALUE => 2,
        \App\Consts\Pay::FIELD_ORDER_KEY    => 'order_id',
        \App\Consts\Pay::FIELD_AMOUNT_KEY   => 'amount',
        \App\Consts\Pay::FIELD_RESPONSE     => 'ok'
    ]
];