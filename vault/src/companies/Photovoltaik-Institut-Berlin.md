```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Photovoltaik-Institut-Berlin" or company = "Photovoltaik Institut Berlin")
sort location, dt_announce desc
```
