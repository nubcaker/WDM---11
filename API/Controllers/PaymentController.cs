﻿using DataModels;
using Infrastructure.Interfaces;
using Microsoft.AspNetCore.Mvc;
using Orleans;
using System;
using System.Threading.Tasks;

namespace API.Controllers
{
    [Route("[controller]")]
    [ApiController]
    public class PaymentController : ControllerBase
    {
   
        private readonly IClusterClient _client;

        public PaymentController(IClusterClient client)
        {
            _client = client;
        }

        [HttpPost("pay/{user_id}/{order_id}/{amount}")]
        public async Task<bool> Pay(Guid user_id, Guid order_id,decimal amount)
        {
            var user = _client.GetGrain<IUserGrain>(user_id);
            var order = _client.GetGrain<IOrderGrain>(order_id);
            var total = await order.GetTotalCost();
            //What to do with amount?
            await user.ChangeCredit(-total);
            return await order.Complete();

            
        }

        [HttpPost("cancel/{user_id}/{order_id}")]
        public async Task<bool> CancelPayment(Guid user_id, Guid order_id)
        {
            var user = _client.GetGrain<IUserGrain>(user_id);
            await user.GetUser();
            var order = _client.GetGrain<IOrderGrain>(order_id);
            var total = await order.GetTotalCost();

            if (await order.CancelComplete())
            {
                await user.ChangeCredit(total);
                return true;
            }

            return false;
        }

        [HttpGet("status/{order_id}")]
        public async Task<Payment> GetStatus(Guid order_id)
        {
            var order = _client.GetGrain<IOrderGrain>(order_id);

            return await order.GetStatus();
        }
    }
}