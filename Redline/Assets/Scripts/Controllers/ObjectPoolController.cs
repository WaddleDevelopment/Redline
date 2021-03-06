﻿using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Generic object pool creator and maintainer.
/// Controllers that require access to large amounts of recycable objects should initiate 
/// this controller with a pool size and request and releast items through it.
/// </summary>


//TODO rewrite this to use the payload design for ObjectPoolItems as in GridItem

//TODO don't make it extend MonoBehaviour. It can be set up like the grid controller. 
public class ObjectPoolController : MonoBehaviour, IEnumerable<FlameController>
{
	private ObjectPoolItem _objectPrefab;
	private int _poolSize;
	private Queue<ObjectPoolItem> _pool;
	private Vector3 _orgScale;

	//TODO write docs
	/// <summary>
	/// 
	/// </summary>
	/// <param name="poolSize"></param>
	/// <param name="itemPrefab"></param>
	/// <exception cref="TypeLoadException"></exception>
	public void Init(int poolSize, ObjectPoolItem itemPrefab)
	{
		_poolSize = poolSize;
		_objectPrefab = itemPrefab;
		_pool = new Queue<ObjectPoolItem>(_poolSize);
		
		if(_objectPrefab == null) throw new TypeLoadException();
		
		for (int i = 0; i < _poolSize; i++)
		{
			ObjectPoolItem newItem = Instantiate( _objectPrefab );
			newItem.transform.SetParent( transform );
			newItem.Disable();
			_pool.Enqueue( newItem );
		}
	}

	public bool ObjectsAvailable()
	{
		return _pool.Count > 0;
	}

	public int ObjectCount()
	{
		return _pool.Count;
	}

	/// <summary>
	/// Returns the oldest ObjectPoolItem in the pool and enables it.
	/// </summary>
	/// <returns>An ObjectPoolItem.</returns>
	public ObjectPoolItem Spawn()
	{
		ObjectPoolItem item = null;
		if ( ObjectsAvailable() )
			item = _pool.Dequeue();
		
		if (item != null)
			item.Enable();
		return item;
	}

	/// <summary>
	/// Deactives and adds an item back into the pool. 
	/// </summary>
	/// <param name="sender"></param>
	public void Remove(ObjectPoolItem sender)
	{
		sender.Disable();
		sender.transform.SetParent( transform );
		_pool.Enqueue(sender);
	}

	private void OnDestroy()
	{
		_pool.Clear();
	}

	public IEnumerator<FlameController> GetEnumerator()
	{
		throw new NotImplementedException();
	}

	IEnumerator IEnumerable.GetEnumerator()
	{
		return _pool.GetEnumerator();
	}

	public int Count()
	{
		return _poolSize;
	}
}
