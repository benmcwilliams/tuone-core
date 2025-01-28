```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "NNB-Generation-Company-(Sizewell-C)-Limited" or company = "NNB Generation Company (Sizewell C) Limited")
sort location, dt_announce desc
```
