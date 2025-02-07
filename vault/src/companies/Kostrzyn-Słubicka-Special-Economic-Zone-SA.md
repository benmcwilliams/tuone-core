```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Kostrzyn-Słubicka-Special-Economic-Zone-SA" or company = "Kostrzyn Słubicka Special Economic Zone SA")
sort location, dt_announce desc
```
