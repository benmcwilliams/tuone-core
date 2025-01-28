```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "IWS-Fleet" or company = "IWS Fleet")
sort location, dt_announce desc
```
