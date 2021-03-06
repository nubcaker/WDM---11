﻿using DataModels;
using Infrastructure.Interfaces;
using Microsoft.AspNetCore.Mvc;
using Orleans;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace API.Controllers
{
    [Route("[controller]")]
    [ApiController]
    public class OrdersController : ControllerBase
    {
        private readonly IClusterClient _client;

        public OrdersController(IClusterClient client)
        {
            _client = client;
        }

        [HttpPost("create/{user_id}")]
        public async Task<OrderFormatted> CreateOrder(Guid user_id)
        {
            var orderId = Guid.NewGuid();
            await _client.GetGrain<IUserGrain>(user_id).GetUser(); //if user does not exist an exception is thrown
            var order = _client.GetGrain<IOrderGrain>(orderId);
            return (await order.CreateOrder(user_id)).GetOrder();
        }
    
        [HttpDelete("remove/{id}")]
        public async Task<bool> RemoveOrder(Guid id)
        {
            //Delete order -> Remove order from user // For now user doesn't have orders
            var order = _client.GetGrain<IOrderGrain>(id);
            return await order.RemoveOrder();
        }

        [HttpGet("find/{id}")]
        public async Task<OrderFormatted> GetOrderDetails(Guid id)
        {
            var order = _client.GetGrain<IOrderGrain>(id);
            return (await order.GetOrder()).GetOrder();
        }

        [HttpPost("additem/{order_id}/{item_id}")]
        public async Task AddItem(Guid order_id, Guid item_id)
        {
            var order = _client.GetGrain<IOrderGrain>(order_id);
            var item = _client.GetGrain<IStockGrain>(item_id);
            await order.AddItem(await item.GetStock());
        }

        [HttpDelete("removeitem/{order_id}/{item_id}")]
        public async Task RemoveItem(Guid order_id, Guid item_id)
        {
            var order = _client.GetGrain<IOrderGrain>(order_id);
            var item = _client.GetGrain<IStockGrain>(item_id);
            await order.RemoveItem(await item.GetStock());
        }

        [HttpPost("checkout/{order_id}")]
        public async Task<ActionResult> Checkout(Guid order_id)
        {
            var order = _client.GetGrain<IOrderGrain>(order_id);
            var result = await order.Checkout();

            if (result)
            {
                var user_id = await order.GetUser();

                var total_cost = await order.GetTotalCost();
                //pay
                var user_grain = _client.GetGrain<IUserGrain>(user_id);

                try
                {
                    await user_grain.ChangeCredit(-total_cost); //This can fail.

                }

                catch (NotEnoughCreditException)
                {
                    await order.CancelCheckout();
                    return NotFound();
                }

                var items = await order.GetItems();
                var success = new List<OrderItem>();
                try
                {
                    foreach (var orderItem in items)
                    {

                        var stock_grain = _client.GetGrain<IStockGrain>(orderItem.Item.ID);
                        await stock_grain.ChangeAmount(-orderItem.Quantity);
                        success.Add(orderItem);


                    }
                }
                catch (InvalidQuantityException)
                {
                    foreach(var orderItem in success)
                    {
                        var stock_grain = _client.GetGrain<IStockGrain>(orderItem.Item.ID);
                        await stock_grain.ChangeAmount(orderItem.Quantity);
                    }
                    await order.CancelCheckout();
                    await user_grain.ChangeCredit(total_cost);
                 
                    return NotFound();
                }

                await order.Complete();
                return Ok();
            }

            return NotFound();

           
        }

    }
}