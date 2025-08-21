<?php
declare(strict_types=1);

namespace App\Pay\Potatoblockpay\Impl;

use App\Entity\PayEntity;
use App\Pay\Base;
use GuzzleHttp\Exception\GuzzleException;
use Kernel\Exception\JSONException;

/**
 * Class Pay
 * @package App\Pay\Kvmpay\Impl
 */
class Pay extends Base implements \App\Pay\Pay
{

    /**
     * @return PayEntity
     * @throws JSONException
     */
    public function trade(): PayEntity
    {

        if (!$this->config['url']) {
            throw new JSONException("请配置网关公网地址");
        }

        if (!$this->config['key']) {
            throw new JSONException("请配置网关密钥");
        }

        $param = [
            'trade_type'   => $this->code,
            'order_id'     => $this->tradeNo,
            'amount'       => $this->amount,
            'notify_url'   => $this->callbackUrl,
            'redirect_url' => $this->returnUrl
        ];

        $param['signature'] = Signature::generateSignature($param, $this->config['key']);

        try {
            $request = $this->http()->post(trim($this->config['url'], "/") . '/submit', [
                "json" => $param, "timeout" => 5,
            ]);
        } catch (GuzzleException $e) {
            throw new JSONException("网关连接失败，下单失败");
        }

        $contents = $request->getBody()->getContents();
        $json     = (array)json_decode((string)$contents, true);
        if ($json['status_code'] != 200) {
            throw new JSONException((string)$json['message']);
        }

        $payEntity = new PayEntity();
        $payEntity->setType(self::TYPE_REDIRECT);
        $payEntity->setUrl($json['payment_url']);

        return $payEntity;
    }
}