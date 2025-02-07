```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Mitsubishi-Fuso-Truck-Europe" or company = "Mitsubishi Fuso Truck Europe")
sort location, dt_announce desc
```
