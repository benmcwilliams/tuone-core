```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and location = "Bóveda, O Saviñao, Paradela, Monforte de Lemos, Pantón and Nogueira de Ramuín"
sort company, dt_announce desc
```
