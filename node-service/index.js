import express from 'express';
import dotenv from 'dotenv';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import { createProxyMiddleware } from 'http-proxy-middleware';

dotenv.config({path:resolve(dirname(fileURLToPath(import.meta.url)),'../.env')});
const app=express();
const port=Number(process.env.PORT||4000);
const django=process.env.DJANGO_URL||'http://localhost:8000';
app.disable('x-powered-by');
app.use(helmet({crossOriginResourcePolicy:{policy:'cross-origin'}}));
app.use(rateLimit({windowMs:60_000,limit:30,standardHeaders:'draft-7',legacyHeaders:false,message:{error:'Too many requests. Please wait a moment and try again.'}}));
app.get('/gateway-health',(_req,res)=>res.json({status:'ok',upstream:django}));
app.use('/api',createProxyMiddleware({target:`${django}/api`,changeOrigin:true,xfwd:true,proxyTimeout:120_000,timeout:120_000,ws:false,on:{error(_err,_req,res){if(res.writeHead)res.writeHead(502,{'Content-Type':'application/json'});res.end(JSON.stringify({error:'The API service is temporarily unavailable.'}));}}}));
app.listen(port,()=>console.log(`QueryQuill gateway listening on ${port}`));
