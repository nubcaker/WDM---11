﻿using Newtonsoft.Json;
using System;

namespace DataModels
{
    [Serializable]
    public class OrderItem
    {
        [JsonProperty(PropertyName = "item")]
        public Stock Item { get; set; } //The available quantity should not be returned. Right ?

        [JsonProperty(PropertyName = "quantity")]
        public int Quantity { get; set; } = 1; // If this exists, its at least 1

        [JsonProperty(PropertyName = "total")]
        public decimal Total => Item.Price * Quantity;

        public void IncQuantity()
        {
            Quantity += 1;
        }

        public void DecQuantity()
        {
            if (Quantity - 1 <= 1)
            {
                throw new InvalidQuantityException();
            }

            Quantity -= 1;
        }
    }
}
