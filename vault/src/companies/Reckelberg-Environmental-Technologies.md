```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Reckelberg-Environmental-Technologies" or company = "Reckelberg Environmental Technologies")
sort location, dt_announce desc
```
