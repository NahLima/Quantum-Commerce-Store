// Dados do catálogo — copiados exatamente do export do Figma Make (src/App.tsx).
// Nomes, categorias, preços, cores, imagens, avaliações e selos são os originais;
// nada foi inventado aqui. Preço, nota e nº de avaliações seguem a mesma fórmula
// do Figma (price = 89 + categoria*37 + índice*28; rating 4.5–4.9; reviews 18+...).

export type Category = 'Tecnologia' | 'Casa' | 'Beleza' | 'Estilo' | 'Outdoor';

export type Product = {
  id: number;
  name: string;
  category: Category;
  price: number;
  color: string;
  image: string;
  rating: number;
  reviews: number;
  badge?: string;
};

export const categories: { name: Category; label: string; description: string }[] = [
  {
    "name": "Tecnologia",
    "label": "Tech",
    "description": "Design que conecta"
  },
  {
    "name": "Casa",
    "label": "Casa",
    "description": "Espaços com intenção"
  },
  {
    "name": "Beleza",
    "label": "Beleza",
    "description": "Cuidado essencial"
  },
  {
    "name": "Estilo",
    "label": "Estilo",
    "description": "Clássicos atuais"
  },
  {
    "name": "Outdoor",
    "label": "Outdoor",
    "description": "Feito para explorar"
  }
];

export const categoryImages: Record<Category, string[]> = {
  "Tecnologia": [
    "https://images.unsplash.com/photo-1613040809024-b4ef7ba99bc3?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1628202926206-c63a34b1618f?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1599669454699-248893623440?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1505740106531-4243f3831c78?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1593121925328-369cc8459c08?auto=format&fit=crop&w=1200&q=85"
  ],
  "Casa": [
    "https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1631679706909-1844bbd07221?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1631510390389-c1e4fb20ff31?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1729086046027-09979ade13fd?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1667312939978-64cf31718a6e?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1618220179428-22790b461013?auto=format&fit=crop&w=1200&q=85"
  ],
  "Beleza": [
    "https://images.unsplash.com/photo-1764694187721-a5035d777fdf?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1779228900994-5b055597a0ec?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1787478187203-7ecefb240b6c?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1771329064159-33f758d91f4a?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1773000129212-3546d5e083cd?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1773070309549-8123488410d7?auto=format&fit=crop&w=1200&q=85"
  ],
  "Estilo": [
    "https://images.unsplash.com/photo-1758887952896-8491d393afe2?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1605583972593-1fda24a7bea2?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1786284684467-2351a5447e8a?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1786284684434-9158964ee63c?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1778521157912-620fd0d3c6e1?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1774389992420-44d11d49f16b?auto=format&fit=crop&w=1200&q=85"
  ],
  "Outdoor": [
    "https://images.unsplash.com/photo-1509762774605-f07235a08f1f?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1592388748465-8c4dca8dd703?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1584895738330-2e2cae9e8355?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1560200772-42d9dcffed6d?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1619689323522-5d1c665dd0f3?auto=format&fit=crop&w=1200&q=85",
    "https://images.unsplash.com/photo-1789067204449-3b0289934627?auto=format&fit=crop&w=1200&q=85"
  ]
};

export const products: Product[] = [
  {
    "id": 1,
    "name": "Fone Orbit Pro",
    "category": "Tecnologia",
    "price": 89,
    "color": "Rosa Névoa",
    "image": "https://images.unsplash.com/photo-1613040809024-b4ef7ba99bc3?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.5,
    "reviews": 18,
    "badge": "Mais vendido"
  },
  {
    "id": 2,
    "name": "Fone Studio One",
    "category": "Tecnologia",
    "price": 117,
    "color": "Cinza Grafite",
    "image": "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.6,
    "reviews": 31
  },
  {
    "id": 3,
    "name": "Óculos Frame",
    "category": "Tecnologia",
    "price": 145,
    "color": "Preto",
    "image": "https://images.unsplash.com/photo-1628202926206-c63a34b1618f?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.7,
    "reviews": 44
  },
  {
    "id": 4,
    "name": "Headphone Eclipse",
    "category": "Tecnologia",
    "price": 173,
    "color": "Noite",
    "image": "https://images.unsplash.com/photo-1599669454699-248893623440?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.8,
    "reviews": 57,
    "badge": "Novo"
  },
  {
    "id": 5,
    "name": "Fone Pulse",
    "category": "Tecnologia",
    "price": 201,
    "color": "Preto Fosco",
    "image": "https://images.unsplash.com/photo-1505740106531-4243f3831c78?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.9,
    "reviews": 70
  },
  {
    "id": 6,
    "name": "Headphone Signal",
    "category": "Tecnologia",
    "price": 229,
    "color": "Rosa Névoa",
    "image": "https://images.unsplash.com/photo-1593121925328-369cc8459c08?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.5,
    "reviews": 83
  },
  {
    "id": 7,
    "name": "Caixa Wave Mini",
    "category": "Tecnologia",
    "price": 257,
    "color": "Cinza Grafite",
    "image": "https://images.unsplash.com/photo-1613040809024-b4ef7ba99bc3?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.6,
    "reviews": 96
  },
  {
    "id": 8,
    "name": "Carregador Arc",
    "category": "Tecnologia",
    "price": 285,
    "color": "Preto",
    "image": "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.7,
    "reviews": 109
  },
  {
    "id": 9,
    "name": "Teclado Flow",
    "category": "Tecnologia",
    "price": 313,
    "color": "Noite",
    "image": "https://images.unsplash.com/photo-1628202926206-c63a34b1618f?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.8,
    "reviews": 122
  },
  {
    "id": 10,
    "name": "Luminária Beam",
    "category": "Tecnologia",
    "price": 341,
    "color": "Preto Fosco",
    "image": "https://images.unsplash.com/photo-1599669454699-248893623440?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.9,
    "reviews": 135
  },
  {
    "id": 11,
    "name": "Poltrona Cloud",
    "category": "Casa",
    "price": 126,
    "color": "Areia",
    "image": "https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.5,
    "reviews": 25,
    "badge": "Mais vendido"
  },
  {
    "id": 12,
    "name": "Sofá Módulo",
    "category": "Casa",
    "price": 154,
    "color": "Off-white",
    "image": "https://images.unsplash.com/photo-1631679706909-1844bbd07221?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.6,
    "reviews": 38
  },
  {
    "id": 13,
    "name": "Cadeira Noma",
    "category": "Casa",
    "price": 182,
    "color": "Verde Sálvia",
    "image": "https://images.unsplash.com/photo-1631510390389-c1e4fb20ff31?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.7,
    "reviews": 51
  },
  {
    "id": 14,
    "name": "Mesa Lateral Loop",
    "category": "Casa",
    "price": 210,
    "color": "Terracota",
    "image": "https://images.unsplash.com/photo-1729086046027-09979ade13fd?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.8,
    "reviews": 64,
    "badge": "Novo"
  },
  {
    "id": 15,
    "name": "Luminária Duna",
    "category": "Casa",
    "price": 238,
    "color": "Madeira Natural",
    "image": "https://images.unsplash.com/photo-1667312939978-64cf31718a6e?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.9,
    "reviews": 77
  },
  {
    "id": 16,
    "name": "Vaso Forma",
    "category": "Casa",
    "price": 266,
    "color": "Areia",
    "image": "https://images.unsplash.com/photo-1618220179428-22790b461013?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.5,
    "reviews": 90
  },
  {
    "id": 17,
    "name": "Manta Brisa",
    "category": "Casa",
    "price": 294,
    "color": "Off-white",
    "image": "https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.6,
    "reviews": 103
  },
  {
    "id": 18,
    "name": "Bandeja Uno",
    "category": "Casa",
    "price": 322,
    "color": "Verde Sálvia",
    "image": "https://images.unsplash.com/photo-1631679706909-1844bbd07221?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.7,
    "reviews": 116
  },
  {
    "id": 19,
    "name": "Difusor Calm",
    "category": "Casa",
    "price": 350,
    "color": "Terracota",
    "image": "https://images.unsplash.com/photo-1631510390389-c1e4fb20ff31?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.8,
    "reviews": 129
  },
  {
    "id": 20,
    "name": "Organizador Grid",
    "category": "Casa",
    "price": 378,
    "color": "Madeira Natural",
    "image": "https://images.unsplash.com/photo-1729086046027-09979ade13fd?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.9,
    "reviews": 142
  },
  {
    "id": 21,
    "name": "Sérum Lumière",
    "category": "Beleza",
    "price": 163,
    "color": "Transparente",
    "image": "https://images.unsplash.com/photo-1764694187721-a5035d777fdf?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.5,
    "reviews": 32,
    "badge": "Mais vendido"
  },
  {
    "id": 22,
    "name": "Óleo Botanical",
    "category": "Beleza",
    "price": 191,
    "color": "Âmbar",
    "image": "https://images.unsplash.com/photo-1779228900994-5b055597a0ec?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.6,
    "reviews": 45
  },
  {
    "id": 23,
    "name": "Kit Essenciais",
    "category": "Beleza",
    "price": 219,
    "color": "Rosé",
    "image": "https://images.unsplash.com/photo-1787478187203-7ecefb240b6c?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.7,
    "reviews": 58
  },
  {
    "id": 24,
    "name": "Sérum Restore",
    "category": "Beleza",
    "price": 247,
    "color": "Natural",
    "image": "https://images.unsplash.com/photo-1771329064159-33f758d91f4a?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.8,
    "reviews": 71,
    "badge": "Novo"
  },
  {
    "id": 25,
    "name": "Máscara Solar",
    "category": "Beleza",
    "price": 275,
    "color": "Coral",
    "image": "https://images.unsplash.com/photo-1773000129212-3546d5e083cd?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.9,
    "reviews": 84
  },
  {
    "id": 26,
    "name": "Cleanser Daily",
    "category": "Beleza",
    "price": 303,
    "color": "Transparente",
    "image": "https://images.unsplash.com/photo-1773070309549-8123488410d7?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.5,
    "reviews": 97
  },
  {
    "id": 27,
    "name": "Hidratante Dew",
    "category": "Beleza",
    "price": 331,
    "color": "Âmbar",
    "image": "https://images.unsplash.com/photo-1764694187721-a5035d777fdf?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.6,
    "reviews": 110
  },
  {
    "id": 28,
    "name": "Balm Aura",
    "category": "Beleza",
    "price": 359,
    "color": "Rosé",
    "image": "https://images.unsplash.com/photo-1779228900994-5b055597a0ec?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.7,
    "reviews": 123
  },
  {
    "id": 29,
    "name": "Essência Calm",
    "category": "Beleza",
    "price": 387,
    "color": "Natural",
    "image": "https://images.unsplash.com/photo-1787478187203-7ecefb240b6c?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.8,
    "reviews": 136
  },
  {
    "id": 30,
    "name": "Protetor Velvet",
    "category": "Beleza",
    "price": 415,
    "color": "Coral",
    "image": "https://images.unsplash.com/photo-1771329064159-33f758d91f4a?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.9,
    "reviews": 149
  },
  {
    "id": 31,
    "name": "Relógio Axis",
    "category": "Estilo",
    "price": 200,
    "color": "Preto",
    "image": "https://images.unsplash.com/photo-1758887952896-8491d393afe2?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.5,
    "reviews": 39,
    "badge": "Mais vendido"
  },
  {
    "id": 32,
    "name": "Relógio Mono",
    "category": "Estilo",
    "price": 228,
    "color": "Prata",
    "image": "https://images.unsplash.com/photo-1605583972593-1fda24a7bea2?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.6,
    "reviews": 52
  },
  {
    "id": 33,
    "name": "Relógio Gild",
    "category": "Estilo",
    "price": 256,
    "color": "Dourado",
    "image": "https://images.unsplash.com/photo-1786284684467-2351a5447e8a?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.7,
    "reviews": 65
  },
  {
    "id": 34,
    "name": "Relógio Verde",
    "category": "Estilo",
    "price": 284,
    "color": "Verde Floresta",
    "image": "https://images.unsplash.com/photo-1786284684434-9158964ee63c?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.8,
    "reviews": 78,
    "badge": "Novo"
  },
  {
    "id": 35,
    "name": "Tênis Modular",
    "category": "Estilo",
    "price": 312,
    "color": "Branco",
    "image": "https://images.unsplash.com/photo-1778521157912-620fd0d3c6e1?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.9,
    "reviews": 91
  },
  {
    "id": 36,
    "name": "Relógio Blanc",
    "category": "Estilo",
    "price": 340,
    "color": "Preto",
    "image": "https://images.unsplash.com/photo-1774389992420-44d11d49f16b?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.5,
    "reviews": 104
  },
  {
    "id": 37,
    "name": "Bolsa Mini Arc",
    "category": "Estilo",
    "price": 368,
    "color": "Prata",
    "image": "https://images.unsplash.com/photo-1758887952896-8491d393afe2?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.6,
    "reviews": 117
  },
  {
    "id": 38,
    "name": "Carteira Fold",
    "category": "Estilo",
    "price": 396,
    "color": "Dourado",
    "image": "https://images.unsplash.com/photo-1605583972593-1fda24a7bea2?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.7,
    "reviews": 130
  },
  {
    "id": 39,
    "name": "Óculos Linear",
    "category": "Estilo",
    "price": 424,
    "color": "Verde Floresta",
    "image": "https://images.unsplash.com/photo-1786284684467-2351a5447e8a?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.8,
    "reviews": 143
  },
  {
    "id": 40,
    "name": "Boné Essential",
    "category": "Estilo",
    "price": 452,
    "color": "Branco",
    "image": "https://images.unsplash.com/photo-1786284684434-9158964ee63c?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.9,
    "reviews": 156
  },
  {
    "id": 41,
    "name": "Mochila Summit",
    "category": "Outdoor",
    "price": 237,
    "color": "Cinza Rocha",
    "image": "https://images.unsplash.com/photo-1509762774605-f07235a08f1f?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.5,
    "reviews": 46,
    "badge": "Mais vendido"
  },
  {
    "id": 42,
    "name": "Mochila Trail",
    "category": "Outdoor",
    "price": 265,
    "color": "Azul Profundo",
    "image": "https://images.unsplash.com/photo-1592388748465-8c4dca8dd703?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.6,
    "reviews": 59
  },
  {
    "id": 43,
    "name": "Mochila Field",
    "category": "Outdoor",
    "price": 293,
    "color": "Preto",
    "image": "https://images.unsplash.com/photo-1584895738330-2e2cae9e8355?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.7,
    "reviews": 72
  },
  {
    "id": 44,
    "name": "Pack Explorer",
    "category": "Outdoor",
    "price": 321,
    "color": "Verde Musgo",
    "image": "https://images.unsplash.com/photo-1560200772-42d9dcffed6d?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.8,
    "reviews": 85,
    "badge": "Novo"
  },
  {
    "id": 45,
    "name": "Mochila Move",
    "category": "Outdoor",
    "price": 349,
    "color": "Violeta",
    "image": "https://images.unsplash.com/photo-1619689323522-5d1c665dd0f3?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.9,
    "reviews": 98
  },
  {
    "id": 46,
    "name": "Garrafa Canyon",
    "category": "Outdoor",
    "price": 377,
    "color": "Cinza Rocha",
    "image": "https://images.unsplash.com/photo-1789067204449-3b0289934627?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.5,
    "reviews": 111
  },
  {
    "id": 47,
    "name": "Lanterna Trek",
    "category": "Outdoor",
    "price": 405,
    "color": "Azul Profundo",
    "image": "https://images.unsplash.com/photo-1509762774605-f07235a08f1f?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.6,
    "reviews": 124
  },
  {
    "id": 48,
    "name": "Copo Térmico Alto",
    "category": "Outdoor",
    "price": 433,
    "color": "Preto",
    "image": "https://images.unsplash.com/photo-1592388748465-8c4dca8dd703?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.7,
    "reviews": 137
  },
  {
    "id": 49,
    "name": "Capa Rain",
    "category": "Outdoor",
    "price": 461,
    "color": "Verde Musgo",
    "image": "https://images.unsplash.com/photo-1584895738330-2e2cae9e8355?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.8,
    "reviews": 150
  },
  {
    "id": 50,
    "name": "Kit Camp",
    "category": "Outdoor",
    "price": 489,
    "color": "Violeta",
    "image": "https://images.unsplash.com/photo-1560200772-42d9dcffed6d?auto=format&fit=crop&w=1200&q=85",
    "rating": 4.9,
    "reviews": 163
  }
];

export function getProduct(id: number): Product | undefined {
  return products.find((p) => p.id === id);
}

export function formatPrice(price: number): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(price);
}
