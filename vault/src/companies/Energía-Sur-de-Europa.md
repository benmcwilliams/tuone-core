```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Energía-Sur-de-Europa" or company = "Energía Sur de Europa")
sort location, dt_announce desc
```
